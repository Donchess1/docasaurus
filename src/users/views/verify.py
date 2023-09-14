from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from core.resources.cache import Cache
from core.resources.email_service import EmailClient
from core.resources.jwt_client import JWTClient
from users import tasks
from users.serializers.register import RegisteredUserPayloadSerializer
from users.serializers.verify_email import (
    ResendOTPSerializer,
    VerifiedOTPPayloadSerializer,
    VerifyOTPSerializer,
)
from utils.response import Response
from utils.utils import (
    EDIT_PROFILE_URL,
    GET_STARTED_BUYER_URL,
    GET_STARTED_SELLER_URL,
    generate_otp,
    generate_temp_id,
)

User = get_user_model()
cache = Cache()


class VerifyOTPView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    jwt_client = JWTClient

    @swagger_auto_schema(
        operation_description="Verify OTP sent to Email",
        responses={
            200: VerifiedOTPPayloadSerializer,
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        otp = serializer.validated_data["otp"]
        temp_id = serializer.validated_data["temp_id"]

        cache_data = cache.get(temp_id)
        if not cache_data or not cache_data["is_valid"]:
            return Response(
                success=False,
                message="OTP expired!",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if cache_data["otp"] != otp:
            return Response(
                success=False,
                message="Invalid OTP!",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        cache_data["is_valid"] = False
        cache.delete(temp_id)

        email = cache_data["email"]
        name = cache_data["name"]
        user = User.objects.get(email=email)
        user.is_verified = True
        user.save()

        dynamic_values = {
            "name": name,
            "recipient": email,
            "get_started_url": GET_STARTED_BUYER_URL
            if user.is_buyer
            else GET_STARTED_BUYER_URL,
        }
        tasks.send_welcome_email(email, dynamic_values)

        token = self.jwt_client.sign(user.id)
        return Response(
            success=True,
            message="Email verified!",
            data={
                "email": email,
                "token": token["access_token"],
            },
            status_code=status.HTTP_200_OK,
        )


class ResendAccountVerificationOTPView(GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Resend OTP sent to Email",
        responses={
            200: RegisteredUserPayloadSerializer,
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data.get("email", None)
        old_temp_id = serializer.validated_data.get("old_temp_id", None)

        user = User.objects.get(email=email)
        name = user.name

        if user.is_verified:
            return Response(
                success=False,
                message="This account has been verified!",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if old_temp_id:
            cache.delete(old_temp_id)

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
        cache.set(otp_key, value, 60 * 60 * 10)

        dynamic_values = {
            "name": name,
            "otp": otp,
            "recipient": email,
            "profile_edit_url": EDIT_PROFILE_URL,
        }
        tasks.send_invitation_email(email, dynamic_values)

        return Response(
            success=True,
            message="OTP has been re-sent",
            data=payload,
            status_code=status.HTTP_200_OK,
        )
