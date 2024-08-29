import os

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.generics import GenericAPIView

from common.serializers.wallet import WalletAmountSerializer
from console import tasks as console_tasks
from console.models import Product, Transaction
from console.serializers.product import (
    GenerateProductPaymentLinkSerializer,
    ProductSerializer,
)
from console.services.product import create_product_purchase_transaction
from core.resources.flutterwave import FlwAPI
from notifications.models.notification import UserNotification
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.response import Response
from utils.text import notifications
from utils.utils import (
    PAYMENT_GATEWAY_PROVIDER,
    add_commas_to_transaction_amount,
    generate_txn_reference,
    parse_datetime,
)

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class ProductViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProductSerializer
    http_method_names = ["get", "post", "put", "delete"]

    def list(self, request):
        products = Product.objects.all()
        serializer = self.serializer_class(products, many=True)
        return Response(
            success=True,
            message="Products retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def create(self, request):
        return self._save_product(request)

    def retrieve(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        serializer = self.serializer_class(product)
        return Response(
            success=True,
            message="Product retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def update(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        return self._save_product(request, instance=product)

    def destroy(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        product.delete()
        return Response(
            success=True,
            message="Product deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    def _save_product(self, request, instance=None):
        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=bool(instance),
            context={"request": request},
        )
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                success=True,
                message="Product created successfully"
                if not instance
                else "Product updated successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
                if not instance
                else status.HTTP_200_OK,
            )
        return Response(
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
        )


class GenerateProductPaymentLinkView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GenerateProductPaymentLinkSerializer

    @transaction.atomic
    def post(self, request, pk=None):
        request_meta = extract_api_request_metadata(request)
        user = request.user
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        product = serializer.validated_data["product"]
        charges = serializer.validated_data["charges"]

        tx_ref = generate_txn_reference()
        txn = create_product_purchase_transaction(
            product, tx_ref, request.user, charges
        )

        description = f"{(user.name).upper()} initiated a purchase of {product.currency} {product.price} for {product.name}. Payment Provider: {PAYMENT_GATEWAY_PROVIDER}"
        log_transaction_activity(txn, description, request_meta)

        tx_data = {
            "tx_ref": tx_ref,
            "amount": product.price,
            "currency": product.currency,
            # "redirect_url": f"{FRONTEND_BASE_URL}/buyer/payment-callback",
            "redirect_url": f"{BACKEND_BASE_URL}/buyer/payment-callback",
            "customer": {
                "email": user.email,
                "phone_number": user.phone,
                "name": user.name,
            },
            "customizations": {
                "title": f"Purchase {product.name}",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            },
            "configurations": {
                "session_duration": 10,
                "max_retry_attempt": 3,
            },
            "meta": {
                "action": "PURCHASE_PRODUCT",
                "product_reference": product.reference,
                "platform": "WEB",
            },
        }

        obj = FlwAPI.initiate_payment_link(tx_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )

        link = obj["data"]["link"]
        payload = {"link": link}

        description = f"Payment link: {link} successfully generated for {product.name} on {PAYMENT_GATEWAY_PROVIDER}."
        log_transaction_activity(txn, description, request_meta)

        return Response(
            success=True,
            message="Payment link successfully generated",
            status_code=status.HTTP_200_OK,
            data=payload,
        )


class ProductPaymentTransactionRedirectView(GenericAPIView):
    serializer_class = WalletAmountSerializer
    permission_classes = [permissions.AllowAny]
    flw_api = FlwAPI

    def get(self, request):
        request_meta = extract_api_request_metadata(request)
        flw_status = request.query_params.get("status", None)
        tx_ref = request.query_params.get("tx_ref", None)
        flw_transaction_id = request.query_params.get("transaction_id", None)

        try:
            txn = Transaction.objects.get(reference=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if txn.verified:
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                message="Payment already verified.",
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.meta.update({"description": f"FLW Transaction cancelled"})
            txn.save()

            description = f"Payment was cancelled."
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment was cancelled.",
            )

        if flw_status == "failed":
            txn.verified = True
            txn.status = "FAILED"
            txn.meta.update({"description": f"FLW Transaction failed"})
            txn.save()

            description = f"Payment failed."
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment failed",
            )

        if flw_status not in ["completed", "successful"]:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid payment status",
            )

        obj = self.flw_api.verify_transaction(flw_transaction_id)

        if obj["status"] == "error":
            msg = obj["message"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()

            description = (
                f"Error occurred while verifying transaction. Description: {msg}"
            )
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()

            description = f"Transaction failed. Description: {msg}"
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )

        if (
            obj["data"]["tx_ref"] == txn.reference
            and obj["data"]["status"] == "successful"
            and obj["data"]["currency"] == txn.currency
            and obj["data"]["charged_amount"] >= txn.amount
        ):
            flw_ref = obj["data"]["flw_ref"]
            narration = obj["data"]["narration"]
            txn.verified = True
            txn.status = "SUCCESSFUL"
            txn.mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = flw_ref
            txn.narration = narration
            payment_type = obj["data"]["payment_type"]
            txn.meta.update(
                {
                    "payment_method": payment_type,
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Transaction {narration}_{flw_ref}",
                }
            )
            txn.save()

            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            description = f"Payment received via {payment_type} channel. Transaction verified via REDIRECT URL."
            log_transaction_activity(txn, description, request_meta)

            try:
                user = User.objects.filter(email=customer_email).first()
                wallet_exists, wallet = user.get_currency_wallet(txn.currency)

                description = f"Previous User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                user.credit_wallet(txn.amount, txn.currency)
                wallet_exists, wallet = user.get_currency_wallet(txn.currency)

                description = f"New User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                email = user.email
                values = {
                    "first_name": user.name.split(" ")[0],
                    "recipient": email,
                    "date": parse_datetime(txn.created_at),
                    "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
                    "wallet_balance": f"{txn.currency} {add_commas_to_transaction_amount(wallet.balance)}",
                    "transaction_reference": f"{(txn.reference).upper()}",
                }
                console_tasks.send_fund_wallet_email.delay(email, values)
                # Create Notification
                UserNotification.objects.create(
                    user=user,
                    category="DEPOSIT",
                    title=notifications.WalletDepositNotification(
                        txn.amount, txn.currency
                    ).TITLE,
                    content=notifications.WalletDepositNotification(
                        txn.amount, txn.currency
                    ).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
                )

                # TODO: Send real-time Notification
            except User.DoesNotExist:
                return Response(
                    success=False,
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                message="Transaction verified.",
            )

        return Response(
            success=True,
            message="Payment successfully verified",
            status_code=status.HTTP_200_OK,
        )
