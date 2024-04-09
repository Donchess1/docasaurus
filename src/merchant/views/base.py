from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action

from merchant.models import Merchant
from merchant.serializers import (
    CustomerUserProfileSerializer,
    MerchantCreateSerializer,
    MerchantDetailSerializer,
    MerchantSerializer,
    RegisterCustomerSerializer,
)
from merchant.utils import validate_request
from users.serializers.user import UserSerializer
from utils.response import Response


class MerchantCreateView(generics.CreateAPIView):
    serializer_class = MerchantCreateSerializer
    queryset = Merchant.objects.all()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        self.perform_create(serializer)
        return Response(
            success=True,
            message="Merchant created successfully",
            status=status.HTTP_201_CREATED,
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


class MerchantProfileView(generics.GenericAPIView):
    serializer_class = MerchantDetailSerializer
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        request_is_valid, resource = validate_request(request)
        if not request_is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message=resource,
            )
        merchant = resource
        serializer = self.get_serializer(merchant)
        return Response(
            success=True,
            message="Merchant profile retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class MerchantResetKeyView(generics.GenericAPIView):
    serializer_class = MerchantSerializer
    permission_classes = (permissions.AllowAny,)

    def put(self, request, *args, **kwargs):
        request_is_valid, resource = validate_request(request)
        if not request_is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message=resource,
            )
        merchant = resource
        merchant.reset_api_key()
        return Response(
            success=True,
            message="API key reset successfully",
            status_code=status.HTTP_200_OK,
        )


class MerchantCustomerView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return RegisterCustomerSerializer
        return self.serializer_class

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
        self.perform_create(serializer)
        return Response(
            success=True,
            message="Customer created successfully",
            status_code=status.HTTP_200_OK,
        )

    def get(self, request, *args, **kwargs):
        request_is_valid, resource = validate_request(request)
        if not request_is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message=resource,
            )
        merchant = resource
        customers = merchant.customer_set.all()
        serialized_customers = CustomerUserProfileSerializer(customers, many=True)
        return Response(
            success=True,
            data=serialized_customers.data,
            message="Customers retrieved successfully",
            status_code=status.HTTP_200_OK,
        )
