from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from core.resources.cache import Cache
from core.resources.email_service import EmailClient
from users import tasks
from users.serializers.register import (
    RegisteredUserPayloadSerializer,
    RegisterSellerSerializer,
)
from utils.kyc import kyc_meta_map
from utils.response import Response
from utils.utils import EDIT_PROFILE_URL, generate_otp, generate_temp_id

User = get_user_model()


class RegisterSellerView(CreateAPIView):
    serializer_class = RegisterSellerSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        return serializer.save()

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

        user = self.perform_create(serializer)
        email = user.email
        name = user.name

        otp = generate_otp()
        otp_key = generate_temp_id()

        payload = {
            "temp_id": otp_key,
            "email": email,
        }
        value = {
            "otp": otp,
            "email": email,
            "name": name,
            "is_valid": True,
        }
        with Cache() as cache:
            cache.set(otp_key, value, 60 * 60 * 10)
        dynamic_values = {
            "name": name,
            "otp": otp,
            "recipient": email,
            "profile_edit_url": EDIT_PROFILE_URL,
        }
        tasks.send_invitation_email.delay(email, dynamic_values)

        return Response(
            success=True,
            message="Verification email sent!",
            data=payload,
            status_code=status.HTTP_201_CREATED,
        )
