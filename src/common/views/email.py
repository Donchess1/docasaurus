from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.email import ValidateEmailAddressSerializer
from utils.email import validate_email_address
from utils.response import Response


class ValidateEmailAddressView(GenericAPIView):
    serializer_class = ValidateEmailAddressSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify Email Address",
        responses={
            200: None,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message=serializer.errors.get("email")[0],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        is_valid, message, validated_response = validate_email_address(
            request.data.get("email"), check_deliverability=True
        )
        if not is_valid:
            return Response(
                success=False,
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            success=True,
            message=message,
            status_code=status.HTTP_200_OK,
            data=validated_response,
        )
