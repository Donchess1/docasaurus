import os

from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action

from merchant.decorators import authorized_api_call
from merchant.models import ApiKey, Customer, CustomerMerchant, Merchant
from merchant.serializers.merchant import (
    ApiKeySerializer,
    CustomerUserProfileSerializer,
    MerchantCreateSerializer,
    MerchantDetailSerializer,
    MerchantSerializer,
    MerchantWalletSerializer,
    RegisterCustomerSerializer,
    UpdateCustomerSerializer,
)
from merchant.utils import generate_api_key
from utils.response import Response
from utils.utils import custom_flatten_uuid, generate_random_text

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class MerchantCreateView(generics.CreateAPIView):
    serializer_class = MerchantCreateSerializer
    queryset = Merchant.objects.all()
    permission_classes = ()

    def perform_create(self, serializer):
        instance_txn_data = serializer.save()
        return instance_txn_data

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        password, _ = self.perform_create(serializer)
        return Response(
            success=True,
            status_code=status.HTTP_201_CREATED,
            message="Merchant created successfully",
            data={"password": password},
        )


class MerchantListView(generics.ListAPIView):
    serializer_class = MerchantSerializer
    queryset = Merchant.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            success=True,
            message="Merchants retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            meta={"count": len(serializer.data)},
        )


class MerchantApiKeyView(generics.GenericAPIView):
    serializer_class = ApiKeySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        merchant = Merchant.objects.filter(user_id=user).first()
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(
            data=request.data,
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        raw_api_key, hashed_api_key = generate_api_key(str(merchant.id))
        name = serializer.validated_data.get("name")
        key_identifier = None

        existing_api_key = ApiKey.objects.filter(merchant=merchant).first()
        if existing_api_key:
            existing_api_key.key = hashed_api_key
            existing_api_key.save()
            key_identifier = str(existing_api_key.id)
        else:
            obj = ApiKey.objects.create(
                key=hashed_api_key, merchant=merchant, name=name
            )
            key_identifier = str(obj.id)

        suffix = f"{generate_random_text(3)}{custom_flatten_uuid(key_identifier)}{raw_api_key}"
        api_key = f"MYBTSTSECK-{suffix}" if env == "test" else f"MYBLIVSECK-{suffix}"

        return Response(
            success=True,
            message="API Key generated successfully. You can only view once.",
            status_code=status.HTTP_200_OK,
            data={"api_key": api_key},
        )


class MerchantProfileView(generics.GenericAPIView):
    serializer_class = MerchantDetailSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_api_call
    def get(self, request, *args, **kwargs):
        merchant = request.merchant
        serializer = self.get_serializer(merchant)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Merchant profile retrieved successfully",
            data=serializer.data,
        )


class MerchantWalletsView(generics.GenericAPIView):
    serializer_class = MerchantWalletSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_api_call
    def get(self, request, *args, **kwargs):
        merchant = request.merchant
        _, wallets = merchant.user_id.get_wallets()
        serializer = self.get_serializer(wallets, many=True)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Merchant wallets retrieved successfully",
            data=serializer.data,
        )


class MerchantCustomerView(generics.CreateAPIView):
    serializer_class = CustomerUserProfileSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return RegisterCustomerSerializer
        return self.serializer_class

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
        self.perform_create(serializer)
        return Response(
            success=True,
            message="Customer created successfully",
            status_code=status.HTTP_200_OK,
        )

    @authorized_api_call
    def get(self, request, *args, **kwargs):
        merchant = request.merchant
        customers = merchant.customer_set.all()
        serialized_customers = self.get_serializer(
            customers,
            many=True,
            context={"merchant": merchant, "hide_wallet_details": True},
        )
        return Response(
            success=True,
            data=serialized_customers.data,
            message="Customers retrieved successfully",
            status_code=status.HTTP_200_OK,
            meta={"count": len(serialized_customers.data)},
        )


class MerchantCustomerDetailView(generics.GenericAPIView):
    serializer_class = CustomerUserProfileSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "PATCH":
            return UpdateCustomerSerializer
        return self.serializer_class

    def perform_update(self, serializer):
        instance = serializer.save()
        return instance

    @authorized_api_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = Customer.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Customer does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance, context={"merchant": merchant})
        return Response(
            success=True,
            message="Customer information retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @authorized_api_call
    def patch(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = Customer.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Customer does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        customer_merchant_instance = CustomerMerchant.objects.filter(
            customer=instance, merchant=merchant
        ).first()
        serializer = self.get_serializer(
            data=request.data,
            context={
                "merchant": merchant,
                "customer_merchant_instance": customer_merchant_instance,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        customer_merchant_instance = self.perform_update(serializer)
        return Response(
            success=True,
            message="Customer information updated successfully",
            status_code=status.HTTP_200_OK,
        )
