import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import GenericAPIView

from common.serializers.wallet import WalletAmountSerializer
from console import tasks as console_tasks
from console.models import Product, TicketPurchase, Transaction
from console.serializers.product import (
    GenerateProductPaymentLinkSerializer,
    ProductSerializer,
    ProductTicketPurchaseSerializer,
    TicketPurchaseAnalyticsSerializer,
)
from console.services.product import create_product_purchase_transaction
from console.utils import IBTE2024_TICKET_TIERS
from core.resources.flutterwave import FlwAPI
from notifications.models.notification import UserNotification
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.models import get_instance_or_404
from utils.pagination import CustomPagination
from utils.response import Response
from utils.text import notifications
from utils.utils import (
    PAYMENT_GATEWAY_PROVIDER,
    add_commas_to_transaction_amount,
    generate_txn_reference,
    generate_txn_reference_v2,
    parse_datetime,
)

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class ProductViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    http_method_names = ["get", "post", "put", "delete"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__name", "user__email", "ticket_product__name"]

    def get_serializer_class(self):
        if self.action in ("get_product_tickets", "get_all_product_tickets"):
            return ProductTicketPurchaseSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ["retrieve", "list", "get_all_product_tickets"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request):
        try:
            queryset = self.get_queryset()
            filtered_queryset = self.filter_queryset(queryset)
            qs = self.paginate_queryset(filtered_queryset)
            serializer = self.get_serializer(qs, many=True)
            self.pagination_class.message = "Products retrieved successfully"
            response = self.get_paginated_response(serializer.data)
            return response

        except DjangoValidationError as e:
            return Response(
                success=False,
                message=f"{str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except DRFValidationError as e:
            return Response(
                success=False,
                message=f"{e.detail}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                success=False,
                message=f"Unexpected error occurred. {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def create(self, request):
        return self._save_product(request)

    def retrieve(self, request, pk=None):
        product = get_instance_or_404(Product, pk)
        serializer = self.serializer_class(product)
        return Response(
            success=True,
            message="Product retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def update(self, request, pk=None):
        product = get_instance_or_404(Product, pk)
        return self._save_product(request, instance=product)

    def destroy(self, request, pk=None):
        product = get_instance_or_404(Product, pk)
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

    @action(detail=True, methods=["get"], url_path="tickets")
    def get_product_tickets(self, request, pk=None):
        product = get_instance_or_404(Product, pk)
        try:
            queryset = TicketPurchase.objects.filter(ticket_product=product).order_by(
                "-created_at"
            )
            qs = self.paginate_queryset(queryset)
            serializer = self.get_serializer(qs, many=True)
            self.pagination_class.message = "Ticket Purchases retrieved successfully"
            response = self.get_paginated_response(serializer.data)
            return response

        except Exception as e:
            return Response(
                success=False,
                message=f"Unexpected error occurred. {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="tickets")
    def get_all_product_tickets(self, request):
        try:
            queryset = TicketPurchase.objects.filter(
                ticket_product__tier__in=IBTE2024_TICKET_TIERS
            ).order_by("-created_at")
            queryset = self.filter_queryset(queryset)
            qs = self.paginate_queryset(queryset)
            serializer = self.get_serializer(qs, many=True)
            self.pagination_class.message = "Ticket Purchases retrieved successfully"
            response = self.get_paginated_response(serializer.data)
            return response

        except Exception as e:
            return Response(
                success=False,
                message=f"Unexpected error occurred. {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
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
        quantity = serializer.validated_data["quantity"]
        charges = serializer.validated_data["charges"]

        if user == product.owner:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="You cannot purchase your own product",
            )

        tx_ref = generate_txn_reference()
        txn = create_product_purchase_transaction(
            product, tx_ref, request.user, charges, quantity
        )

        description = f"{(user.name).upper()} initiated a purchase of {product.currency} {product.price} for {product.name}. Payment Provider: {PAYMENT_GATEWAY_PROVIDER}"
        log_transaction_activity(txn, description, request_meta)

        product_total = product.price * quantity
        total_amount = product_total + charges

        tx_data = {
            "tx_ref": tx_ref,
            "amount": total_amount,
            "currency": product.currency,
            "redirect_url": f"{FRONTEND_BASE_URL}/ibtx",
            # "redirect_url": f"{BACKEND_BASE_URL}/v1/shared/product-payment-redirect",
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
                "ticket_quantity": quantity,
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
        payload = {"link": link, "amount_payable": total_amount, "tx_ref": tx_ref}

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

    @transaction.atomic
    def get(self, request):
        request_meta = extract_api_request_metadata(request)
        flw_status = request.query_params.get("status", None)
        tx_ref = request.query_params.get("tx_ref", None)
        flw_transaction_id = request.query_params.get("transaction_id", None)

        if not tx_ref:
            return Response(
                success=False,
                message="Transaction reference missing",
                status_code=status.HTTP_400_BAD_REQUEST,
                data={
                    "message_header": "Transaction Error!",
                    "message_body": "Transaction reference missing",
                },
            )

        try:
            txn = Transaction.objects.get(reference=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
                data={
                    "message_header": "Transaction Error!",
                    "message_body": " This transaction does not exist!",
                },
            )

        product = txn.product
        product_name = product.name

        if txn.verified:
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                message="Payment already verified.",
                data={
                    "message_header": "Thank You For Your Purchase!",
                    "message_body": f"Your ticket to the {product_name} has already been processed. Please check your email for your ticket code and further instructions.",
                },
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
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"Unfortunately, we are unable to process your ticket. Your payment was cancelled. Please try again.",
                },
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
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"Unfortunately, we are unable to process your ticket. Your payment failed. Please try again.",
                },
            )

        if flw_status not in ["completed", "successful"]:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid payment status",
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"Invalid payment status. Please try again.",
                },
            )

        obj = self.flw_api.verify_transaction(flw_transaction_id)
        description = f"Attempted to verify transaction {flw_transaction_id} on Flutterwave via API."
        log_transaction_activity(txn, description, request_meta)

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
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"An error occurred while processing your ticket payment. Please contact support with this reference: {txn.reference}.",
                },
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
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"An error occurred while processing your ticket payment. Please contact support with this reference: {txn.reference}.",
                },
            )

        description = f"Successfully verified transaction {flw_transaction_id} on Flutterwave via API."
        log_transaction_activity(txn, description, request_meta)

        txn_reference_match = obj["data"]["tx_ref"] == txn.reference
        txn_currency_match = obj["data"]["currency"] == txn.currency
        txn_success_match = obj["data"]["status"] in ("successful", "completed")
        txn_valid_charged_amount_match = obj["data"]["charged_amount"] >= txn.amount

        if not (
            txn_reference_match
            and txn_success_match
            and txn_currency_match
            and txn_valid_charged_amount_match
        ):
            description = f"Error occurred while verifying transaction. Mismatch with transactionReferenceMatch: {txn_reference_match}. currencyMatch: {txn_currency_match}. successMatch: {txn_success_match}. validChargedAmountMatch: {txn_valid_charged_amount_match}."
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Transaction Error!",
                data={
                    "message_header": "Transaction Error!",
                    "message_body": f"An error occurred while processing your ticket payment. Please contact support with this reference: {txn.reference}.",
                },
            )

        flw_ref = obj["data"]["flw_ref"]
        narration = obj["data"]["narration"]
        txn.verified = True
        txn.status = "SUCCESSFUL"
        txn.provider_mode = obj["data"]["auth_model"]
        txn.charge = obj["data"]["app_fee"]
        txn.remitted_amount = obj["data"]["amount_settled"]
        txn.provider_tx_reference = flw_ref
        txn.narration = narration
        payment_type = obj["data"]["payment_type"]
        payment_type = payment_type.replace("_", " ").title()
        txn.meta.update(
            {
                "payment_method": payment_type,
                "provider_txn_id": obj["data"]["id"],
            }
        )
        txn.save()

        customer_email = obj["data"]["customer"]["email"]
        amount_charged = obj["data"]["charged_amount"]
        meta = obj["data"].get("meta")
        ticket_quantity = meta.get("ticket_quantity")

        description = f"Payment received via {payment_type} channel. Transaction verified via REDIRECT URL."
        log_transaction_activity(txn, description, request_meta)

        product_owner = product.owner
        wallet_exists, owner_wallet = product_owner.get_currency_wallet(txn.currency)

        settlement_ref = generate_txn_reference()
        Transaction.objects.create(
            type="SETTLEMENT",
            status="SUCCESSFUL",
            user_id=product_owner,
            reference=settlement_ref,
            provider="MYBALANCE",
            provider_tx_reference=settlement_ref,
            mode="WEB",
            currency=txn.currency,
            amount=txn.amount,
            charge=txn.charge,
            product=product,
            meta={"description": "Product Merchant Settlement"},
            verified=True,
        )

        description = f"Previous Product Merchant Balance: {txn.currency} {add_commas_to_transaction_amount(owner_wallet.balance)}"
        log_transaction_activity(txn, description, request_meta)

        product_owner.credit_wallet(txn.amount, txn.currency)
        wallet_exists, owner_wallet = product_owner.get_currency_wallet(txn.currency)

        description = f"New Product Merchant Balance: {txn.currency} {add_commas_to_transaction_amount(owner_wallet.balance)}"
        log_transaction_activity(txn, description, request_meta)

        user = User.objects.filter(email=customer_email).first()
        email = user.email
        tier_mapping = {"BASIC": "BSC", "VIP": "VIP", "VVIP": "VVIP"}
        product_tier = (product.tier).split("-")[0]  # "BASIC-DEFAULT", "BASIC-TEST"
        tier_code = tier_mapping.get(product_tier, "")
        event_ticket_code = f"MYB{tier_code}-{generate_txn_reference_v2()}"
        values = {
            "name": user.name,
            "phone_number": user.phone,
            "first_name": user.name.split(" ")[0],
            "recipient": email,
            "date": parse_datetime(txn.created_at),
            "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
            "transaction_reference": f"{(txn.reference).upper()}",
            "event_ticket_code": event_ticket_code,
            "event_name": product.event.name,
            "ticket_quantity": f"x{ticket_quantity}",
            "event_date_time": parse_datetime(product.event.date),
            "event_ticket_type": product.name,
            "event_venue": product.event.venue,
            "payment_type": payment_type,
            "product_unit_price": f"{product.currency} {add_commas_to_transaction_amount(product.price)}",
        }
        console_tasks.send_product_ticket_successful_payment_email.delay(email, values)
        # Create Notification
        ticket_details = {
            "event_name": product.event.name,
            "event_date_time": product.event.date,
            "event_ticket_type": product.name,
            "event_venue": product.event.venue,
            "ticket_quantity": product.quantity,
            "event_ticket_price": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
            "event_ticket_code": event_ticket_code,
        }
        UserNotification.objects.create(
            user=user,
            category="PRODUCT_PURCHASE_SUCCESSFUL",
            title=notifications.ProductTicketSuccessfulPaymentNotification(
                txn.amount, txn.currency, ticket_details
            ).TITLE,
            content=notifications.ProductTicketSuccessfulPaymentNotification(
                txn.amount, txn.currency, ticket_details
            ).CONTENT,
            action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
        )
        # Create ticket purchase instance
        TicketPurchase.objects.create(
            user=txn.user_id,
            ticket_product=product,
            transaction=txn,
            ticket_code=event_ticket_code,
        )
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Transaction verified.",
            data={
                "message_header": "Thank You For Your Purchase!",
                "message_body": f"Your payment for {product_name} was processed successfully. Please check your email for your ticket code and further instructions.",
            },
        )


class TicketPurchaseAnalyticsView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TicketPurchaseAnalyticsSerializer

    def get(self, request):
        aggregated_data = TicketPurchase.objects.values(
            "ticket_product__name",
            "ticket_product__reference",
            "ticket_product__event__name",
        ).annotate(purchase_count=Count("id"))

        analytics_data = [
            {
                "event": item["ticket_product__event__name"],
                "ticket_name": item["ticket_product__name"],
                "reference": item["ticket_product__reference"],
                "count": item["purchase_count"],
            }
            for item in aggregated_data
        ]

        serializer = self.serializer_class(analytics_data, many=True)
        return Response(
            success=True,
            data=serializer.data,
            message=f"Ticket Purchase Metrics Retrieved Successfully",
            status_code=status.HTTP_200_OK,
        )
