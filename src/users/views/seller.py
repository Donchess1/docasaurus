from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from core.resources.cache import Cache
from core.resources.email_service import EmailClient
from users import tasks
from users.serializers.kyc import kyc_meta_map
from users.serializers.register import (
    RegisteredUserPayloadSerializer,
    RegisterSellerSerializer,
)
from utils.response import Response
from utils.utils import EDIT_PROFILE_URL, generate_otp, generate_temp_id

User = get_user_model()
cache = Cache()


class RegisterSellerView(CreateAPIView):
    serializer_class = RegisterSellerSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a Seller",
        responses={
            200: RegisteredUserPayloadSerializer,
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

        kyc_type = serializer.validated_data["kyc_type"]
        kyc_meta = serializer.validated_data["kyc_meta"]

        kyc_meta_serializer = kyc_meta_map.get(kyc_type)(data=kyc_meta)
        if not kyc_meta_serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"kyc_meta": kyc_meta_serializer.errors},
            )

        self.perform_create(serializer)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        name = serializer.validated_data["name"]

        otp = generate_otp()
        otp_key = generate_temp_id()

        payload = {
            "temp_id": otp_key,
        }
        value = {
            "otp": otp,
            "email": email,
            "name": name,
            "is_valid": True,
        }
        cache.set(otp_key, value, 60 * 60 * 10)
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        dynamic_values = {
            "name": name,
            "otp": otp,
            "recipient": email,
            "profile_edit_url": EDIT_PROFILE_URL,
        }
        tasks.send_invitation_email(email, dynamic_values)

        return Response(
            success=True,
            message="Verification email sent!",
            data=payload,
            status_code=status.HTTP_201_CREATED,
        )
