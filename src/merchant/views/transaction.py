import os
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.flutterwave import FlwAPI
from merchant.decorators import authorized_api_call
from merchant.models import CustomerMerchant, Merchant, PayoutConfig
from merchant.serializers.transaction import (
    CreateMerchantEscrowTransactionSerializer,
    MandateFundsReleaseSerializer,
    MerchantEscrowRedirectPayloadSerializer,
    MerchantTransactionSerializer,
    ReleaseEscrowTransactionByMerchantSerializer,
    UnlockCustomerEscrowTransactionByBuyerSerializer,
)
from merchant.utils import (
    create_bulk_merchant_escrow_transactions,
    get_customer_merchant_instance,
    get_merchant_by_id,
    get_merchant_escrow_users,
    get_merchant_users_redirect_url,
    validate_request,
)
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from users.serializers.user import UserSerializer
from utils.pagination import CustomPagination
from utils.response import Response
from utils.text import notifications
from utils.transaction import (
    get_merchant_escrow_transaction_stakeholders,
    release_escrow_funds_by_merchant,
)
from utils.utils import add_commas_to_transaction_amount, parse_date, parse_datetime

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
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
    @authorized_api_call
    def list(self, request, *args, **kwargs):
        merchant = request.merchant
        queryset = self.get_queryset().filter(merchant=merchant, type="ESCROW")
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Transactions retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response


class MerchantSettlementTransactionListView(generics.ListAPIView):
    serializer_class = MerchantTransactionSerializer
    queryset = Transaction.objects.filter().order_by("-created_at")
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "provider", "type"]

    @swagger_auto_schema(
        operation_description="List Merchant Settlements",
        responses={
            200: MerchantTransactionSerializer,
        },
    )
    @authorized_api_call
    def list(self, request, *args, **kwargs):
        merchant = request.merchant
        queryset = self.get_queryset().filter(
            merchant=merchant, type="MERCHANT_SETTLEMENT"
        )
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Settlements retrieved successfully"
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
    @authorized_api_call
    def post(self, request, *args, **kwargs):
        merchant = request.merchant
        serializer = self.get_serializer(
            data=request.data, context={"merchant": merchant}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        flw_init_txn_data, payment_breakdown = self.perform_create(serializer)
        obj = self.flw_api.initiate_payment_link(flw_init_txn_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )

        payload = {"link": obj["data"]["link"], "payment_breakdown": payment_breakdown}
        return Response(
            success=True,
            status_code=status.HTTP_201_CREATED,
            data=payload,
            message="Escrow transaction initiated",
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
            total_payable_amount_to_charge = obj["data"]["meta"]["total_payable_amount"]
            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            user = User.objects.filter(email=customer_email).first()
            if not user:
                return Response(
                    success=False,
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            user.credit_wallet(amount_charged, txn.currency)
            user.debit_wallet(total_payable_amount_to_charge, txn.currency)
            user.update_locked_amount(
                amount=txn.amount,
                currency=txn.currency,
                mode="OUTWARD",
                type="CREDIT",
            )

            escrow_entities = txn.meta.get("seller_escrow_breakdown")
            payout_config_id = txn.meta.get("payout_config")
            payout_config = PayoutConfig.objects.filter(id=payout_config_id).first()
            merchant_id = txn.meta.get("merchant")
            merchant = get_merchant_by_id(merchant_id)

            # create bulk escrow transactions from entities data
            escrows = create_bulk_merchant_escrow_transactions(
                merchant, user, escrow_entities, txn, payout_config, txn.currency
            )
            products = []
            for transaction in escrows:
                escrow_users = get_merchant_escrow_users(transaction, merchant)
                seller: CustomerMerchant = escrow_users.get("seller")
                products.append(
                    {
                        "name": transaction.escrowmeta.item_type,
                        "quantity": transaction.escrowmeta.item_quantity,
                        "amount": f"{txn.currency} {add_commas_to_transaction_amount(str(transaction.amount))}",
                        "store_owner": seller.alternate_name,
                    }
                )
            buyer_values = {
                "date": parse_datetime(txn.updated_at),
                "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(str(amount_charged))}",
                "merchant_platform": merchant.name,
                "products": products,
            }
            txn_tasks.send_lock_funds_merchant_buyer_email.delay(
                user.email, buyer_values
            )
            amt = add_commas_to_transaction_amount(str(amount_charged))
            UserNotification.objects.create(
                user=user,
                category="FUNDS_LOCKED_BUYER",
                title=notifications.FundsLockedBuyerNotification(
                    amt, txn.currency
                ).TITLE,
                content=notifications.FundsLockedBuyerNotification(
                    amt, txn.currency
                ).CONTENT,
                action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{txn.reference}",
            )

        buyer_redirect_url = None
        redirect_urls = get_merchant_users_redirect_url(merchant)
        if redirect_urls:
            buyer_redirect_url = redirect_urls.get("buyer_redirect_url")

        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            data={
                "transaction_reference": txn.reference,
                "amount": total_payable_amount_to_charge,
                "redirect_url": buyer_redirect_url
                if buyer_redirect_url
                else f"{FRONTEND_BASE_URL}/login",
            },
            message="Transaction verified.",
        )


class MandateFundsReleaseView(generics.CreateAPIView):
    serializer_class = MandateFundsReleaseSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return Transaction.objects.all()

    @swagger_auto_schema(
        operation_description="Mandate release of escrow funds",
        responses={
            200: None,
        },
    )
    @authorized_api_call
    def post(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = (
            self.get_queryset().filter(id=id, merchant=merchant, type="ESCROW").first()
        )
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist or is invalid",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.escrowmeta.buyer_consent_to_unlock:
            return Response(
                success=False,
                message="Mandate for release has already been granted.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if instance.status == "FUFILLED":
            return Response(
                success=False,
                message="Transaction has already been fulfilled.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        today = timezone.now().date()
        if instance.escrowmeta.delivery_date > today:
            return Response(
                success=False,
                message="Delivery date has not elapsed.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.serializer_class(
            data=request.data,
            context={
                "merchant": merchant,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        buyer_email = serializer.validated_data.get("buyer_email")
        stakeholders = get_merchant_escrow_transaction_stakeholders(id)
        if buyer_email != stakeholders["BUYER"]:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="Only buyer can mandate release of funds",
            )

        instance.escrowmeta.buyer_consent_to_unlock = True
        instance.escrowmeta.save()

        # TODO: Send out email notification to buyer, seller and merchant

        return Response(
            status=True,
            message="Funds release mandated successfully",
            status_code=status.HTTP_200_OK,
        )


class ReleaseEscrowFundsByMerchantView(generics.GenericAPIView):
    serializer_class = ReleaseEscrowTransactionByMerchantSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return Transaction.objects.all()

    @swagger_auto_schema(
        operation_description="Unlock Escrow Transaction Funds",
        responses={
            200: None,
        },
    )
    @authorized_api_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = (
            self.get_queryset().filter(id=id, merchant=merchant, type="ESCROW").first()
        )
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist or is invalid",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not instance.escrowmeta.buyer_consent_to_unlock:
            return Response(
                success=False,
                message="Mandate for release has not been granted.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if instance.status == "FUFILLED":
            return Response(
                success=False,
                message="Transaction has already been fulfilled.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()
        if instance.escrowmeta.delivery_date > today:
            return Response(
                success=False,
                message="Delivery date has not elapsed.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        successful, message = release_escrow_funds_by_merchant(instance)
        return Response(
            status=True,
            message="Funds unlocked successfully",
            status_code=status.HTTP_200_OK,
        )


class UnlockEscrowFundsByBuyerView(generics.CreateAPIView):
    serializer_class = UnlockCustomerEscrowTransactionByBuyerSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Transaction.objects.all()

    def perform_create(self, serializer):
        return serializer.save()

    @swagger_auto_schema(
        operation_description="Unlock Escrow Transaction Funds",
        responses={
            200: None,
        },
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        merchant_id = request.query_params.get("merchant")
        if not merchant_id:
            return Response(
                success=False,
                message="Merchant ID is required. Pass 'merchant' in query parameters",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        merchant_customer = get_customer_merchant_instance(user.email, merchant)
        if not merchant_customer:
            return Response(
                success=False,
                message="Customer does not exist for merchant",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if merchant_customer.user_type != "BUYER":
            return Response(
                success=False,
                message="Only a buyer can unlock funds",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.serializer_class(
            data=request.data,
            context={
                "merchant": merchant,
                "user": user,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        completed, message = self.perform_create(serializer)
        return (
            Response(
                status=True,
                message=message,
                status_code=status.HTTP_200_OK,
            )
            if completed
            else Response(
                status=False,
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        )
