from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.driver_license import (
    ValidatedDriverLicensePayloadSerializer,
    ValidateDriverLicenseSerializer,
)
from core.resources.third_party.main import ThirdPartyAPI
from utils.response import Response


class ValidateDriverLicenseView(GenericAPIView):
    serializer_class = ValidateDriverLicenseSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI

    @swagger_auto_schema(
        operation_description="Verify Driver's License",
        responses={
            200: ValidatedDriverLicensePayloadSerializer,
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

        obj = self.third_party.validate_driver_license(data)
        if not obj["status"]:
            return Response(
                success=False,
                status_code=status.HTTP_404_NOT_FOUND,
                message=obj["message"],
            )

        return Response(
            success=True,
            message=obj["message"],
            status_code=status.HTTP_200_OK,
            data=obj["payload"],
        )
