import re

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from core.resources.cache import Cache
from core.resources.jwt_client import JWTClient
from users import tasks
from users.models.profile import UserProfile
from users.serializers.register import RegisteredUserPayloadSerializer
from users.serializers.verify_email import (
    ResendOTPSerializer,
    VerifiedOTPPayloadSerializer,
    VerifyOTPSerializer,
)
from users.services import handle_successful_login
from utils.response import Response
from utils.utils import (
    EDIT_PROFILE_URL,
    GET_STARTED_BUYER_URL,
    GET_STARTED_SELLER_URL,
    MERCHANT_DASHBOARD_URL,
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
        cache_data = None
        with Cache() as cache:
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
        with Cache() as cache:
            cache.delete(temp_id)

        email = cache_data["email"]
        name = cache_data["name"]
        user = User.objects.get(email=email)
        user.is_verified = True
        user.save()

        get_started_url = ""
        if user.is_seller:
            get_started_url = GET_STARTED_SELLER_URL
        elif user.is_buyer:
            get_started_url = GET_STARTED_BUYER_URL
        elif user.is_merchant:
            get_started_url = MERCHANT_DASHBOARD_URL

        dynamic_values = {
            "name": name,
            "recipient": email,
            "get_started_url": get_started_url,
        }
        tasks.send_onboarding_successful_email.delay(email, dynamic_values)
        data = handle_successful_login(user)
        return Response(
            success=True,
            message="Email verified!",
            data=data,
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
                message="This account has already been verified!",
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
        with Cache() as cache:
            cache.set(otp_key, value, 60 * 10)
        dynamic_values = {
            "name": name,
            "otp": otp,
            "recipient": email,
            "profile_edit_url": EDIT_PROFILE_URL,
        }
        tasks.send_invitation_email.delay(email, dynamic_values)

        return Response(
            success=True,
            message="OTP has been re-sent",
            data=payload,
            status_code=status.HTTP_200_OK,
        )


class VerifyOneTimeLoginCodeView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

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
        cache_data = None
        with Cache() as cache:
            cache_data = cache.get(temp_id)
        if not cache_data or not cache_data["is_valid"]:
            return Response(
                success=False,
                message="One Time Code expired! Please try again",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if cache_data["otp"] != otp:
            return Response(
                success=False,
                message="Invalid One Time Code. Please try again",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        cache_data["is_valid"] = False
        with Cache() as cache:
            cache.delete(temp_id)

        email = cache_data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                success=False,
                message="User information not found!",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_verified:
            return Response(
                success=False,
                message="Your email is not verified yet",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        profile = UserProfile.objects.filter(user_id=user).first()
        if not profile:
            return Response(
                success=False,
                message="Profile not set. Contact Support.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        data = handle_successful_login(user)
        return Response(
            success=True,
            message="Login successful",
            data=data,
            status_code=status.HTTP_200_OK,
        )
