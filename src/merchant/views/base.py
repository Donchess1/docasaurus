import os

from django.db.models import Prefetch
from django_filters import rest_framework as django_filters
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from console.permissions import IsSuperAdmin
from console.serializers.base import EmptySerializer
from merchant.decorators import authorized_api_call
from merchant.filters import MerchantFilter
from merchant.models import ApiKey, Customer, CustomerMerchant, Merchant
from merchant.serializers.merchant import (
    ApiKeySerializer,
    CustomerUserProfileSerializer,
    MerchantCreateSerializer,
    MerchantSerializer,
    MerchantWalletSerializer,
    RegisterCustomerSerializer,
    UpdateCustomerSerializer,
)
from merchant.utils import generate_api_key
from utils.pagination import CustomPagination
from utils.response import Response
from utils.utils import custom_flatten_uuid, generate_random_text

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class MerchantCreateView(generics.CreateAPIView):
    serializer_class = MerchantCreateSerializer
    queryset = Merchant.objects.all()
    permission_classes = (IsSuperAdmin,)

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
    permission_classes = (IsSuperAdmin,)
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = MerchantFilter
    search_fields = ["name", "user_id__email", "user_id__name"]
    ordering_fields = ["name", "created_at", "user_id__email", "user_id__name"]
    pagination_class = CustomPagination

    def get_queryset(self):
        return (
            Merchant.objects.select_related("user_id__userprofile")
            .all()
            .order_by("-created_at")
        )

    def get_ordering(self):
        custom_ordering_map = {
            "email": "user_id__email",  # Frontend uses 'email', we map it to 'user_id__email'
            "owner": "user_id__name",  # Frontend uses 'user_name', we map to 'user_id__name'
        }
        ordering_param = self.request.query_params.get("ordering", None)
        if ordering_param:
            ordering_fields = []
            for field in ordering_param.split(","):
                stripped_field = field.lstrip("-")  # Remove '-' to check field name
                prefix = "-" if field.startswith("-") else ""
                mapped_field = custom_ordering_map.get(stripped_field, stripped_field)
                ordering_fields.append(f"{prefix}{mapped_field}")
            return ordering_fields
        return ["-created_at"]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            ordering = self.get_ordering()
            if ordering:
                queryset = queryset.order_by(*ordering)
            qs = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                qs,
                context={"hide_wallet_details": True},
                many=True,
            )
            self.pagination_class.message = "Merchants retrieved successfully."
            response = self.get_paginated_response(serializer.data)
            return response
        except Exception as e:
            return Response(
                success=False,
                message=f"{str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class MerchantDetailView(generics.GenericAPIView):
    serializer_class = MerchantSerializer
    permission_classes = (IsSuperAdmin,)

    def get(self, request, id, *args, **kwargs):
        instance = Merchant.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Merchant retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class ConsoleMerchantCustomerView(generics.ListAPIView):
    serializer_class = CustomerUserProfileSerializer
    permission_classes = (IsSuperAdmin,)
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # filterset_class = MerchantFilter
    search_fields = [
        "user__name",  # Search by User's name
        "user__email",  # Search by User's email
        "customermerchant__alternate_name",  # Search by CustomerMerchant alternate_name
        "customermerchant__alternate_email",  # Search by CustomerMerchant alternate_email
        "customermerchant__user_type",  # Search by CustomerMerchant user_type
    ]
    # ordering_fields = ["created_at", "user__email", "user__name"]
    pagination_class = CustomPagination

    def get_queryset(self):
        merchant_id = self.kwargs.get("id")
        merchant = Merchant.objects.filter(id=merchant_id).first()
        if not merchant:
            raise NotFound(detail="Merchant does not exist")

        # Prefetch related CustomerMerchant and select related User profile
        queryset = (
            Customer.objects.filter(merchants=merchant)
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "customermerchant_set",
                    queryset=CustomerMerchant.objects.filter(merchant=merchant),
                    to_attr="custom_customermerchant",
                )
            )
        )
        return queryset

    def get(self, request, id, *args, **kwargs):
        merchant = Merchant.objects.filter(id=id).first()
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serialized_customers = self.get_serializer(
            qs,
            context={"merchant": merchant, "hide_wallet_details": True},
            many=True,
        )
        self.pagination_class.message = "Customers retrieved successfully."
        response = self.get_paginated_response(serialized_customers.data)
        return response


class ConsoleGenerateMerchantApiKeyView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = (IsSuperAdmin,)

    def post(self, request, id, *args, **kwargs):
        merchant = Merchant.objects.filter(id=id).first()
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        raw_api_key, hashed_api_key = generate_api_key(str(merchant.id))
        name = generate_random_text(10)
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


class MerchantApiKeyView(generics.GenericAPIView):
    serializer_class = ApiKeySerializer
    permission_classes = (IsSuperAdmin,)

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
    serializer_class = MerchantSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_api_call
    def get(self, request, *args, **kwargs):
        merchant = request.merchant
        serializer = self.get_serializer(
            merchant, context={"hide_wallet_details": True}
        )
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
