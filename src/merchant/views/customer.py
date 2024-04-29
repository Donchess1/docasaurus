import os

from django.db.models import OuterRef, Q, Subquery
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import action

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.cache import Cache
from core.resources.jwt_client import JWTClient
from merchant import tasks
from merchant.decorators import authorized_api_call
from merchant.models import Merchant
from merchant.serializers.dispute import MerchantEscrowDisputeSerializer
from merchant.serializers.merchant import (
    CustomerWidgetSessionPayloadSerializer,
    CustomerWidgetSessionSerializer,
)
from merchant.serializers.transaction import (
    ConfirmMerchantWalletWithdrawalSerializer,
    InitiateMerchantWalletWithdrawalSerializer,
    MerchantTransactionSerializer,
)
from merchant.utils import (
    get_customer_merchant_instance,
    get_merchant_by_id,
    initiate_gateway_withdrawal_transaction,
    validate_request,
    verify_otp,
)
from utils.pagination import CustomPagination
from utils.response import Response
from utils.transaction import get_merchant_escrow_transaction_stakeholders
from utils.utils import (
    add_commas_to_transaction_amount,
    generate_otp,
    generate_random_text,
    generate_temp_id,
    generate_txn_reference,
    get_withdrawal_fee,
)

CUSTOMER_WIDGET_BUYER_BASE_URL = os.environ.get("CUSTOMER_WIDGET_BUYER_BASE_URL", "")
CUSTOMER_WIDGET_SELLER_BASE_URL = os.environ.get("CUSTOMER_WIDGET_SELLER_BASE_URL", "")

cache = Cache()


class CustomerWidgetSessionView(generics.GenericAPIView):
    serializer_class = CustomerWidgetSessionSerializer
    permission_classes = (permissions.AllowAny,)
    jwt_client = JWTClient

    @swagger_auto_schema(
        operation_description="Generate Customer Widget Session URL",
        responses={
            201: CustomerWidgetSessionPayloadSerializer,
        },
    )
    @authorized_api_call
    def post(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = Merchant.objects.filter(id=merchant_id).first()
        serializer = self.serializer_class(
            data=request.data,
            context={
                "merchant": merchant,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        res = serializer.validated_data
        obj = res.get("customer_instance")
        user = obj.customer.user
        user_type = obj.user_type
        token = self.jwt_client.sign(user.id)
        access_key = token["access_token"]
        payload = {
            "session_lifetime": "120MINS",
            "url": f"{CUSTOMER_WIDGET_BUYER_BASE_URL}/{generate_random_text(36)}{str(merchant.id)}{access_key}{generate_random_text(4)}"
            if user_type == "BUYER"
            else f"{CUSTOMER_WIDGET_SELLER_BASE_URL}/{generate_random_text(36)}{str(merchant.id)}{access_key}{generate_random_text(4)}",
        }
        return Response(
            success=True,
            message="Widget session created successfully",
            status_code=status.HTTP_201_CREATED,
            data=payload,
        )


class CustomerTransactionListView(generics.ListAPIView):
    serializer_class = MerchantTransactionSerializer
    queryset = Transaction.objects.filter().order_by("-created_at")
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "customer"]

    @swagger_auto_schema(
        operation_description="Get Customer Transactions",
        responses={
            200: MerchantTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        customer_email = request.user.email
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
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        merchant_customer = get_customer_merchant_instance(customer_email, merchant)
        if not merchant_customer:
            return Response(
                success=False,
                message="Customer does not exist for merchant",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        merchant_transactions_queryset = self.get_queryset().filter(
            merchant=merchant, type="ESCROW"
        )
        customer_queryset = merchant_transactions_queryset.filter(
            Q(escrowmeta__partner_email=customer_email)
            | Q(escrowmeta__meta__parties__buyer=customer_email)
            | Q(escrowmeta__meta__parties__seller=customer_email)
        ).distinct()
        # Subquery to get the related LockedAmount for each transaction.
        # This confirms that escrow payment has been made and verified.
        locked_amount_subquery = LockedAmount.objects.filter(
            transaction=OuterRef("pk")
        ).values("transaction")
        customer_queryset = customer_queryset.annotate(
            has_locked_amount=Subquery(locked_amount_subquery)
        ).filter(has_locked_amount__isnull=False)
        data = customer_queryset.filter(status="SUCCESSFUL")
        filtered_queryset = self.filter_queryset(
            customer_queryset.filter(status="SUCCESSFUL")
        )
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Transactions retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response


class CustomerTransactionDetailView(generics.GenericAPIView):
    serializer_class = MerchantTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Transaction.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return MerchantEscrowDisputeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        instance_txn_data = serializer.save()
        return instance_txn_data

    @swagger_auto_schema(
        operation_description="Get A Customer transaction detail by ID",
        responses={
            200: MerchantTransactionSerializer,
        },
    )
    def get(self, request, id, *args, **kwargs):
        instance = self.get_queryset().filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        stakeholders = get_merchant_escrow_transaction_stakeholders(id)
        if request.user.email not in stakeholders.values():
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to view this transaction",
            )

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Transaction detail retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="Create dispute for merchant escrow transaction.",
        responses={
            201: MerchantEscrowDisputeSerializer,
        },
    )
    def post(self, request, id, *args, **kwargs):
        instance = self.get_queryset().filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        stakeholders = get_merchant_escrow_transaction_stakeholders(id)
        if request.user.email not in stakeholders.values():
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to raise dispute for this transaction",
            )

        user_type = ""
        for key, value in stakeholders.items():
            if value == request.user.email:
                user_type = key
                break

        serializer = self.get_serializer(
            data=request.data,
            context={
                "transaction": instance,
                "user": request.user,
                "author": user_type,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        dispute = self.perform_create(serializer)
        ser = MerchantEscrowDisputeSerializer(dispute)
        return Response(
            success=True,
            message="Dispute created successfully",
            status_code=status.HTTP_201_CREATED,
            data=ser.data,
        )


class InitiateMerchantWalletWithdrawalView(generics.GenericAPIView):
    serializer_class = InitiateMerchantWalletWithdrawalSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="Initiate withdrawal from seller dashboard",
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(
            data=request.data,
            context={
                "user": user,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        otp = generate_otp()
        otp_key = generate_temp_id()

        payload = {
            "temp_id": otp_key,
        }
        value = {
            "otp": otp,
            "data": dict(data),
            "is_valid": True,
        }
        cache.set(otp_key, value, 60 * 60 * 10)

        merchant_platform = data.get("merchant_platform")
        amount = data.get("amount")

        dynamic_values = {
            "otp": otp,
            "merchant_platform": merchant_platform,
            "expiry_time_minutes": "10 minutes",
            "action_description": f"confirm withdrawal of NGN {add_commas_to_transaction_amount(int(amount))} from your wallet",
        }
        tasks.send_merchant_wallet_withdrawal_confirmation_email(
            user.email, dynamic_values
        )

        return Response(
            success=True,
            message="Withdrawal initiated",
            status_code=status.HTTP_200_OK,
            data=payload,
        )


class ConfirmMerchantWalletWithdrawalView(generics.GenericAPIView):
    serializer_class = ConfirmMerchantWalletWithdrawalSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="Confirm wallet withdrawal on merchant widget",
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(
            data=request.data,
            context={
                "user": user,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        otp = data.get("otp")
        temp_id = data.get("temp_id")

        is_valid, resource = verify_otp(otp, temp_id)
        if not is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=resource,
            )
        print("CACHE DATA", resource)
        data = resource.get("data")
        successful, resource = initiate_gateway_withdrawal_transaction(user, data)
        return (
            Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=resource,
            )
            if not successful
            else Response(
                success=True,
                message="Withdrawal is currently being processed",
                status_code=status.HTTP_200_OK,
                data=resource,
            )
        )
