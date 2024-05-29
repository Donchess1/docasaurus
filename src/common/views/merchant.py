from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status

from common.serializers.merchant import (
    TrimMerchantTokenPayloadSerializer,
    TrimMerchantTokenSerializer,
)
from core.resources.jwt_client import JWTClient
from merchant.utils import verify_merchant_widget_token_key
from utils.response import Response

User = get_user_model()


class TrimMerchantTokenView(generics.GenericAPIView):
    serializer_class = TrimMerchantTokenSerializer
    permission_classes = (permissions.AllowAny,)
    jwt_client = JWTClient

    @swagger_auto_schema(
        operation_description="Deconstruct Merchant Widget Token",
        responses={
            200: TrimMerchantTokenPayloadSerializer,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        key = data.get("key")
        is_valid, resource = verify_merchant_widget_token_key(key)
        if not is_valid:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=resource,
            )
        merchant_id = resource.get("merchant_id")
        token = resource.get("access_key")
        user_id = self.jwt_client.authenticate_token(token)
        user, customer_email = None, None
        if not user_id:
            return Response(
                success=False,
                message="Invalid token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(id=user_id).first()
        payload = {
            "token": token,
            "merchant_id": merchant_id,
            "customer_email": user.email,
        }
        return Response(
            success=True,
            message="Conversion complete.",
            status_code=status.HTTP_200_OK,
            data=payload,
        )
