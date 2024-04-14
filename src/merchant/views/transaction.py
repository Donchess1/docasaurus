import os
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.flutterwave import FlwAPI
from merchant.models import Merchant
from merchant.serializers.transaction import (
    CreateMerchantEscrowTransactionSerializer,
    MerchantEscrowRedirectPayloadSerializer,
    MerchantTransactionSerializer,
)
from merchant.utils import get_merchant_escrow_users, validate_request
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from users.serializers.user import UserSerializer
from utils.pagination import CustomPagination
from utils.response import Response
from utils.text import notifications
from utils.utils import add_commas_to_transaction_amount, parse_date, parse_datetime

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
User = get_user_model()


class MerchantTransactionListView(generics.ListAPIView):
    serializer_class = MerchantTransactionSerializer
    queryset = Transaction.objects.filter().order_by("-created_at")
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "provider", "type"]

    @swagger_auto_schema(
        operation_description="List Merchant Transactions",
        responses={
            200: MerchantTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        request_is_valid, resource = validate_request(request)
        if not request_is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message=resource,
            )
        merchant = resource
        queryset = self.get_queryset().filter(merchant=merchant)
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Transactions retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response


class InitiateMerchantEscrowTransactionView(generics.CreateAPIView):
    serializer_class = CreateMerchantEscrowTransactionSerializer
    permission_classes = (permissions.AllowAny,)
    flw_api = FlwAPI

    def perform_create(self, serializer):
        instance_txn_data = serializer.save()
        return instance_txn_data

    @swagger_auto_schema(
        operation_description="Initiate Merchant Escrow Transaction",
        responses={
            200: None,
        },
    )
    def post(self, request, *args, **kwargs):
        request_is_valid, resource = validate_request(request)
        if not request_is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message=resource,
            )
        merchant = resource
        serializer = self.get_serializer(
            data=request.data, context={"merchant": merchant}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        instance_txn_data = self.perform_create(serializer)
        obj = self.flw_api.initiate_payment_link(instance_txn_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )

        payload = {"link": obj["data"]["link"]}
        return Response(
            success=True,
            status_code=status.HTTP_201_CREATED,
            data=payload,
            message="Escrow Transaction initiated",
        )


class MerchantEscrowTransactionRedirectView(generics.GenericAPIView):
    serializer_class = MerchantEscrowRedirectPayloadSerializer
    permission_classes = (permissions.AllowAny,)
    flw_api = FlwAPI

    def get(self, request):
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
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Transaction already verified",
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.meta.update({"description": f"FLW Escrow Transaction cancelled"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment was cancelled.",
            )

        if flw_status == "failed":
            txn.verified = True
            txn.status = "FAILED"
            txn.meta.update({"description": f"FLW Escrow Transaction failed"})
            txn.save()
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
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}[]",
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}",
            )

        if (
            obj["data"]["tx_ref"] == txn.reference
            and obj["data"]["status"] == "successful"
            and obj["data"]["currency"] == txn.currency
            and obj["data"]["charged_amount"] >= txn.amount
        ):
            escrow_txn_ref = obj["data"]["meta"]["escrow_transaction_reference"]
            escrow_txn = Transaction.objects.filter(reference=escrow_txn_ref).first()
            escrow_txn.verified = True
            escrow_txn.status = "SUCCESSFUL"
            escrow_txn.save()
            escrow_amount_to_charge = int(escrow_txn.amount + escrow_txn.charge)

            flw_ref = obj["data"]["flw_ref"]
            narration = obj["data"]["narration"]
            txn.verified = True
            txn.status = "SUCCESSFUL"
            txn.mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = flw_ref
            txn.narration = narration
            txn.meta.update(
                {
                    "payment_method": obj["data"]["payment_type"],
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Escrow Transaction {narration}_{flw_ref}",
                }
            )
            txn.save()
            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]
            try:
                user = User.objects.get(email=customer_email)
                profile = user.userprofile
                profile.wallet_balance += int(amount_charged)
                profile.locked_amount += int(escrow_txn.amount)
                profile.save()
                profile.wallet_balance -= Decimal(str(escrow_amount_to_charge))
                profile.save()

                seller_email = escrow_txn.escrowmeta.meta.get("parties")["seller"]
                instance = LockedAmount.objects.create(
                    transaction=escrow_txn,
                    user=user,
                    seller_email=seller_email,
                    amount=escrow_txn.amount,
                    status="ESCROW",
                )
                instance.save()

                merchant = escrow_txn.merchant
                escrow_users = get_merchant_escrow_users(escrow_txn, merchant)
                buyer = escrow_users.get("buyer")
                seller = escrow_users.get("seller")

                # Notify Buyer via email address and in-app
                buyer_values = {
                    "recipient": user.email,
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"NGN {add_commas_to_transaction_amount(str(escrow_amount_to_charge))}",
                    "transaction_id": f"{(escrow_txn.reference).upper()}",
                    "item_name": escrow_txn.meta.get("title"),
                    "merchant_platform": merchant.name,
                    "seller_name": seller.alternate_name,
                }
                txn_tasks.send_lock_funds_merchant_buyer_email(user.email, buyer_values)
                UserNotification.objects.create(
                    user=user,
                    category="FUNDS_LOCKED_BUYER",
                    title=notifications.FUNDS_LOCKED_BUYER_TITLE,
                    content=notifications.FUNDS_LOCKED_BUYER_CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                )

                seller_values = {
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"NGN {add_commas_to_transaction_amount(escrow_txn.amount)}",
                    "transaction_id": f"{(escrow_txn.reference).upper()}",
                    "item_name": escrow_txn.meta.get("title"),
                    "delivery_date": parse_date(escrow_txn.escrowmeta.delivery_date),
                    "buyer_name": buyer.alternate_name,
                    "buyer_phone": buyer.alternate_phone_number,
                    "buyer_email": buyer.customer.user.email,
                    "merchant_platform": merchant.name,
                }
                txn_tasks.send_lock_funds_merchant_seller_email(
                    seller_email, seller_values
                )
                # Create Notification for Seller
                UserNotification.objects.create(
                    user=seller.customer.user,
                    category="FUNDS_LOCKED_SELLER",
                    title=notifications.FUNDS_LOCKED_CONFIRMATION_TITLE,
                    content=notifications.FUNDS_LOCKED_CONFIRMATION_CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                )

                merchant_values = {
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"NGN {add_commas_to_transaction_amount(str(escrow_amount_to_charge))}",
                    "transaction_id": (escrow_txn.reference).upper(),
                    "item_name": escrow_txn.meta["title"],
                    "delivery_date": parse_date(escrow_txn.escrowmeta.delivery_date),
                    "seller_name": seller.alternate_name,
                    "seller_phone": seller.alternate_phone_number,
                    "seller_email": seller.customer.user.email,
                    "buyer_name": buyer.alternate_name,
                    "buyer_phone": buyer.alternate_phone_number,
                    "buyer_email": buyer.customer.user.email,
                    "merchant_platform": escrow_txn.merchant.name,
                }
                txn_tasks.send_lock_funds_merchant_email(
                    merchant.user_id.email, merchant_values
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
            data={
                "transaction_reference": escrow_txn_ref,
                "amount": escrow_amount_to_charge,
                "redirect_url": escrow_txn.merchant.escrow_redirect_url
                or f"{BACKEND_BASE_URL}/swagger-api-docs",
            },
            message="Transaction verified.",
        )
