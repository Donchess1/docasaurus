from rest_framework import generics, permissions, status

from console.permissions import IsSuperAdmin
from console.serializers.provider import EmailProviderSwitchSerializer
from core.resources.email_service_v2 import EmailClientV2
from utils.response import Response


class EmailProviderSwitchView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = EmailProviderSwitchSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        provider = serializer.validated_data.get("provider")
        try:
            EmailClientV2.set_provider(provider)
            return Response(
                success=True,
                message="Email Provider updated successfully",
                data={"provider": EmailClientV2.PROVIDER},
                status_code=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response(
                success=False,
                message=str(e),
                data=serializer.data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
