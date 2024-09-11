import os
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters import rest_framework as django_filters
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
    create_bulk_merchant_transactions_and_products_and_log_activity,
    get_customer_merchant_instance,
    get_merchant_by_id,
    get_merchant_escrow_users,
    get_merchant_users_redirect_url,
    validate_request,
)
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from transaction.filters import TransactionFilter
from transaction.models import TransactionActivityLog
from transaction.serializers.activity_log import TransactionActivityLogSerializer
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.pagination import CustomPagination
from utils.response import Response
from utils.text import notifications
from utils.transaction import (
    get_escrow_transaction_users,
    get_merchant_escrow_transaction_stakeholders,
    get_transaction_instance,
    release_escrow_funds_by_merchant,
)
from utils.utils import (
    PAYMENT_GATEWAY_PROVIDER,
    add_commas_to_transaction_amount,
    parse_date,
    parse_datetime,
)

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
User = get_user_model()


class MerchantTransactionListView(generics.ListAPIView):
    serializer_class = MerchantTransactionSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TransactionFilter
    search_fields = ["reference", "provider", "type"]
    throttle_scope = "merchant_api"

    @swagger_auto_schema(
        operation_description="List Merchant Transactions",
        responses={
            200: None,
        },
    )
    @authorized_api_call
    def list(self, request, *args, **kwargs):
        merchant = request.merchant
        queryset = Transaction.objects.filter(
            type__in=["DEPOSIT", "ESCROW", "WITHDRAW"], merchant=merchant
        ).order_by("-created_at")
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(
            qs, context={"hide_escrow_details": True}, many=True
        )
        self.pagination_class.message = "Transactions retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response


class MerchantTransactionDetailView(generics.GenericAPIView):
    serializer_class = MerchantTransactionSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_api_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Forbidden action",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, context={"merchant": merchant})
        return Response(
            success=True,
            message="Transaction retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )


class MerchantTransactionActivityLogView(generics.ListAPIView):
    serializer_class = TransactionActivityLogSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_api_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Forbidden action",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        qs = TransactionActivityLog.objects.filter(transaction=instance).order_by(
            "created_at"
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(
            success=True,
            message="Transaction activity logs retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )


class MerchantSettlementTransactionListView(generics.ListAPIView):
    serializer_class = MerchantTransactionSerializer
    queryset = Transaction.objects.filter().order_by("-created_at")
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TransactionFilter
    search_fields = ["reference", "provider", "type"]
    throttle_scope = "merchant_api"

    @swagger_auto_schema(
        operation_description="List Merchant Settlements",
        responses={
            200: None,
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
        serializer = self.get_serializer(
            qs, context={"hide_escrow_details": True}, many=True
        )
        self.pagination_class.message = "Settlements retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response


class InitiateMerchantEscrowTransactionView(generics.CreateAPIView):
    serializer_class = CreateMerchantEscrowTransactionSerializer
    permission_classes = (permissions.AllowAny,)
    flw_api = FlwAPI
    throttle_scope = "merchant_api"

    def perform_create(self, serializer):
        instance_txn_data = serializer.save()
        return instance_txn_data

    @authorized_api_call
    def post(self, request, *args, **kwargs):
        request_meta = extract_api_request_metadata(request)
        merchant = request.merchant
        serializer = self.get_serializer(
            data=request.data,
            context={"merchant": merchant, "request_meta": request_meta},
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        deposit_txn, flw_init_txn_data, payment_breakdown = self.perform_create(
            serializer
        )
        obj = self.flw_api.initiate_payment_link(flw_init_txn_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )

        link = obj["data"]["link"]
        payload = {"link": link, "payment_breakdown": payment_breakdown}

        description = f"Payment link: {link} successfully generated on {PAYMENT_GATEWAY_PROVIDER}."
        log_transaction_activity(deposit_txn, description, request_meta)

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
    throttle_scope = "merchant_api"

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

        buyer_redirect_url = None
        redirect_urls = get_merchant_users_redirect_url(txn.merchant)
        if redirect_urls:
            buyer_redirect_url = redirect_urls.get("buyer_redirect_url")

        if txn.verified:
            total_payable_amount_to_charge = txn.meta.get(
                "total_payable_amount_to_charge"
            )
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                message="Transaction successfully verified",
                data={
                    "transaction_reference": txn.reference,
                    "amount": total_payable_amount_to_charge,
                    "redirect_url": buyer_redirect_url
                    if buyer_redirect_url
                    else f"{FRONTEND_BASE_URL}/login",
                },
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.meta.update({"description": f"FLW Escrow Transaction cancelled"})
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
            txn.meta.update({"description": f"FLW Escrow Transaction failed"})
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
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
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
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
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
            txn.provider_mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = flw_ref
            txn.narration = narration
            payment_type = obj["data"]["payment_type"]
            total_payable_amount_to_charge = obj["data"]["meta"]["total_payable_amount"]
            txn.meta.update(
                {
                    "payment_method": payment_type,
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Escrow Transaction {narration}_{flw_ref}",
                    "total_payable_amount_to_charge": total_payable_amount_to_charge,
                }
            )
            txn.save()
            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            description = f"Payment received via {payment_type} channel. Transaction verified via REDIRECT URL."
            log_transaction_activity(txn, description, request_meta)

            user = User.objects.filter(email=customer_email).first()
            if not user:
                return Response(
                    success=False,
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            _, wallet = user.get_currency_wallet(txn.currency)

            description = f"Previous Sender Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)

            user.credit_wallet(amount_charged, txn.currency)
            _, wallet = user.get_currency_wallet(txn.currency)

            description = f"Sender Balance after topup: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)

            user.debit_wallet(total_payable_amount_to_charge, txn.currency)
            user.update_locked_amount(
                amount=txn.amount,
                currency=txn.currency,
                mode="OUTWARD",
                type="CREDIT",
            )

            _, wallet = user.get_currency_wallet(txn.currency)
            description = f"New Sender Balance after final debit: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)

            (
                products,
                escrow_references,
            ) = create_bulk_merchant_transactions_and_products_and_log_activity(
                txn, user, request_meta
            )
            buyer_values = {
                "date": parse_datetime(txn.updated_at),
                "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(amount_charged)}",
                "merchant_platform": txn.merchant.name,
                "products": products,
            }
            txn_tasks.send_lock_funds_merchant_buyer_email.delay(
                user.email, buyer_values
            )
            amt = add_commas_to_transaction_amount(amount_charged)
            for ref in escrow_references:
                UserNotification.objects.create(
                    user=user,
                    category="FUNDS_LOCKED_BUYER",
                    title=notifications.FundsLockedBuyerNotification(
                        amt, txn.currency
                    ).TITLE,
                    content=notifications.FundsLockedBuyerNotification(
                        amt, txn.currency
                    ).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{ref}",
                )

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
    throttle_scope = "merchant_api"

    @swagger_auto_schema(
        operation_description="Mandate release of escrow funds",
        responses={
            200: None,
        },
    )
    @authorized_api_call
    def post(self, request, id, *args, **kwargs):
        request_meta = extract_api_request_metadata(request)
        merchant = request.merchant
        instance = get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist or is invalid",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Forbidden action",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if instance.type != "ESCROW":
            return Response(
                success=False,
                message="Invalid escrow transaction.",
                status_code=status.HTTP_400_BAD_REQUEST,
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

        escrow_users = get_escrow_transaction_users(instance)
        buyer = escrow_users["BUYER"]
        buyer_name = buyer["name"]
        buyer_email = buyer["email"]

        description = f"{buyer_name.upper()} <{buyer_email}> [SENDER/BUYER] gave consent to release of escrow funds."
        log_transaction_activity(instance, description, request_meta)

        # TODO: Send out email notification to buyer, seller and merchant

        return Response(
            status=True,
            message="Funds release mandated successfully",
            status_code=status.HTTP_200_OK,
        )


class ReleaseEscrowFundsByMerchantView(generics.GenericAPIView):
    serializer_class = ReleaseEscrowTransactionByMerchantSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @swagger_auto_schema(
        operation_description="Unlock Escrow Transaction Funds",
        responses={
            200: None,
        },
    )
    @authorized_api_call
    def get(self, request, id, *args, **kwargs):
        request_meta = extract_api_request_metadata(request)
        merchant = request.merchant
        instance = get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Forbidden action",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if instance.type != "ESCROW":
            return Response(
                success=False,
                message="Invalid escrow transaction.",
                status_code=status.HTTP_400_BAD_REQUEST,
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

        successful, message = release_escrow_funds_by_merchant(instance, request_meta)
        return Response(
            success=True if successful else False,
            message=message,
            status_code=status.HTTP_200_OK
            if successful
            else status.HTTP_400_BAD_REQUEST,
        )


class UnlockEscrowFundsByBuyerView(generics.CreateAPIView):
    serializer_class = UnlockCustomerEscrowTransactionByBuyerSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = "merchant_api"

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
        request_meta = extract_api_request_metadata(request)
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
                "request_meta": request_meta,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        completed, message = self.perform_create(serializer)
        return Response(
            success=True if completed else False,
            message=message,
            status_code=status.HTTP_200_OK
            if completed
            else status.HTTP_400_BAD_REQUEST,
        )
