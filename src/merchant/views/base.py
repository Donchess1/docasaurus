from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action

from merchant.decorators import authorized_api_call
from merchant.models import ApiKey, Merchant
from merchant.serializers.merchant import (
    ApiKeySerializer,
    CustomerUserProfileSerializer,
    MerchantCreateSerializer,
    MerchantDetailSerializer,
    MerchantSerializer,
    RegisterCustomerSerializer,
)
from merchant.utils import generate_api_key
from users.serializers.user import UserSerializer
from utils.response import Response


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

        existing_api_key = ApiKey.objects.filter(merchant=merchant).first()
        if existing_api_key:
            existing_api_key.key = hashed_api_key
            existing_api_key.save()
        else:
            ApiKey.objects.create(key=hashed_api_key, merchant=merchant, name=name)

        return Response(
            success=True,
            message="API Key generated successfully. You can only view once.",
            status_code=status.HTTP_200_OK,
            data={"api_key": raw_api_key},
        )


class MerchantProfileView(generics.GenericAPIView):
    serializer_class = MerchantDetailSerializer
    permission_classes = (permissions.AllowAny,)

    @authorized_api_call
    def get(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = Merchant.objects.filter(id=merchant_id).first()
        serializer = self.get_serializer(merchant)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Merchant profile retrieved successfully",
            data=serializer.data,
        )


class MerchantCustomerView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return RegisterCustomerSerializer
        return self.serializer_class

    @authorized_api_call
    def post(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = Merchant.objects.filter(id=merchant_id).first()
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
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = Merchant.objects.filter(id=merchant_id).first()
        customers = merchant.customer_set.all()
        serialized_customers = CustomerUserProfileSerializer(
            customers, many=True, context={"merchant": merchant}
        )
        return Response(
            success=True,
            data=serialized_customers.data,
            message="Customers retrieved successfully",
            status_code=status.HTTP_200_OK,
        )
