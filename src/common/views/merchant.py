from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status

from common.serializers.merchant import (
    TrimMerchantTokenPayloadSerializer,
    TrimMerchantTokenSerializer,
)
from utils.response import Response
from utils.utils import deconstruct_merchant_widget_key


class TrimMerchantTokenView(generics.GenericAPIView):
    serializer_class = TrimMerchantTokenSerializer
    permission_classes = (permissions.AllowAny,)

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
        key = data.get("key", None)
        payload = deconstruct_merchant_widget_key(key)
        if not payload:
            return Response(
                success=False,
                message="Invalid key provided",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            success=True,
            message="Conversion complete.",
            status_code=status.HTTP_200_OK,
            data=payload,
        )
