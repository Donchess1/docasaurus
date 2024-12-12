import os

from django.db.models import Q
from django_filters import rest_framework as django_filters
from rest_framework import filters, generics, permissions, status

from console.models.dispute import Dispute
from dispute.filters import DisputeFilter
from dispute.serializers.dispute import DisputeSerializer
from merchant.decorators import authorized_merchant_apikey_or_token_call
from merchant.utils import get_customer_merchant_instance
from utils.pagination import CustomPagination
from utils.response import Response


class MerchantDisputeListView(generics.ListAPIView):
    serializer_class = DisputeSerializer
    queryset = Dispute.objects.all().order_by("-created_at")
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = DisputeFilter
    search_fields = [
        "merchant__user__email",
        "buyer__email",
        "seller__email",
        "transaction__reference",
    ]
    throttle_scope = "merchant_api"

    @authorized_merchant_apikey_or_token_call
    def list(self, request, *args, **kwargs):
        merchant = request.merchant
        queryset = self.get_queryset().filter(merchant=merchant)
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(
            qs,
            many=True,
        )
        self.pagination_class.message = "Disputes retrieved successfully"
        return self.get_paginated_response(serializer.data)


class MerchantDisputeDetailView(generics.GenericAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_merchant_apikey_or_token_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = Dispute.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Dispute does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Dispute not viewable by merchant",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, context={"merchant": merchant})
        return Response(
            success=True,
            message="Dispute retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )


class MerchantDashboardCustomerDisputeListView(generics.ListAPIView):
    serializer_class = DisputeSerializer
    queryset = Dispute.objects.all().order_by("-created_at")
    permission_classes = (permissions.AllowAny,)
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = DisputeFilter
    search_fields = [
        "transaction__reference",
    ]
    throttle_scope = "merchant_api"

    @authorized_merchant_apikey_or_token_call
    def list(self, request, *args, **kwargs):
        merchant = request.merchant
        customer_email = request.query_params.get("customer_email")
        if not customer_email:
            return Response(
                success=False,
                message="Customer email is required. Pass 'customer_email' in query parameters",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        merchant_customer = get_customer_merchant_instance(customer_email, merchant)
        if not merchant_customer:
            return Response(
                success=False,
                message="Customer does not exist for merchant",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        queryset = (
            self.get_queryset()
            .filter(merchant=merchant)
            .filter(Q(buyer__email=customer_email) | Q(seller__email=customer_email))
            .distinct()
        )
        filtered_queryset = self.filter_queryset(queryset)
        qs = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(
            qs,
            many=True,
        )
        self.pagination_class.message = "Customer disputes retrieved successfully"
        return self.get_paginated_response(serializer.data)


class MerchantDashboardCustomerDisputeDetailView(generics.GenericAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "merchant_api"

    @authorized_merchant_apikey_or_token_call
    def get(self, request, id, *args, **kwargs):
        merchant = request.merchant
        instance = Dispute.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Dispute does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Dispute not viewable by merchant",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, context={"merchant": merchant})
        return Response(
            success=True,
            message="Dispute retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
