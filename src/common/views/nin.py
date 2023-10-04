from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.bvn import ValidateNINBVNSerializer
from common.serializers.nin import ValidatedNINPayloadSerializer
from console.models.identity import NINIdentity
from console.serializers.identity import NINIdentitySerializer
from core.resources.third_party.main import ThirdPartyAPI
from utils.response import Response


class ValidateNINView(GenericAPIView):
    serializer_class = ValidateNINBVNSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI

    @swagger_auto_schema(
        operation_description="Verify National Identification Number (NIN)",
        responses={
            200: ValidatedNINPayloadSerializer,
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
        number = data.get("number", None)
        instance = NINIdentity.objects.filter(number=number).first()
        if instance:
            serializer = NINIdentitySerializer(instance)
            return Response(
                success=True,
                message="Verification Successful",
                status_code=status.HTTP_200_OK,
                data=serializer.data,
            )

        obj = self.third_party.validate_NIN(number)
        if not obj.get("data", None) or obj.get("status") == "error":
            message = obj.get("msg", "Verification failed. Provide a valid NIN number")
            return Response(
                success=False,
                status_code=status.HTTP_404_NOT_FOUND,
                message=message,
            )
        data = obj.get("data")
        created_instance = NINIdentity.objects.create(
            number=number, meta=data, provider="ZEEHAFRICA"
        )
        serializer = NINIdentitySerializer(created_instance)

        return Response(
            success=True,
            message="Verification successful",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
