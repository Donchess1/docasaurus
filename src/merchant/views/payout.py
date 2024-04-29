from rest_framework import status, viewsets

from merchant.decorators import authorized_api_call
from merchant.models.base import PayoutConfig
from merchant.serializers.merchant import PayoutConfigSerializer
from merchant.utils import get_merchant_by_id
from utils.response import Response


class PayoutConfigViewSet(viewsets.ModelViewSet):
    queryset = PayoutConfig.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "delete"]
    serializer_class = PayoutConfigSerializer

    @authorized_api_call
    def create(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(
            data=request.data, context={"merchant": merchant}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        existing_active_config = PayoutConfig.objects.filter(
            merchant=merchant, is_active=True
        ).first()
        if existing_active_config:
            existing_active_config.is_active = False
            existing_active_config.save()
        serializer.save(merchant=merchant)
        return Response(
            success=True,
            status_code=status.HTTP_201_CREATED,
            data=serializer.data,
            message="Payout Config Created",
        )

    @authorized_api_call
    def list(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        queryset = self.queryset.filter(merchant=merchant)
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            message="Payout Config retrieved successfully",
        )

    @authorized_api_call
    def retrieve(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        instance = self.get_object()
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Payout config does not belong to this merchant",
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            message="Payout Config retrieved successfully",
        )

    @authorized_api_call
    def destroy(self, request, *args, **kwargs):
        merchant_id = request.headers.get("X-IDENTITY")
        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            return Response(
                success=False,
                message="Merchant does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        instance = self.get_object()
        if instance.merchant != merchant:
            return Response(
                success=False,
                message="Payout config does not belong to this merchant",
                status=status.HTTP_403_FORBIDDEN,
            )
        if instance.is_active:
            return Response(
                success=False,
                message="Active payout configuration cannot be deleted",
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(
            success=True,
            message="Payout config deleted successfully",
            status=status.HTTP_204_NO_CONTENT,
        )
