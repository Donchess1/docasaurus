from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.resources.cache import Cache
from core.resources.email_service import EmailClient
from users import tasks
from users.serializers.password import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from utils.response import Response
from utils.utils import (
    RESET_PASSWORD_URL,
    generate_otp,
    generate_random_text,
    generate_temp_id,
)

User = get_user_model()
cache = Cache()


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request to reset User Password",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]

        user = User.objects.get(email=email)
        name = user.name

        otp = generate_otp()
        otp_key = generate_random_text(80)

        value = {
            "otp": otp,
            "email": email,
            "is_valid": True,
        }

        cache.set(otp_key, value, 60 * 60 * 15)  # OTP/Token expires in 15 minutes

        dynamic_values = {
            "first_name": name.split(" ")[0],
            "recipient": email,
            "password_reset_link": f"{RESET_PASSWORD_URL}/{otp_key}",
        }
        tasks.send_reset_password_request_email.delay(email, dynamic_values)

        return Response(
            success=True,
            message="Password reset email has been sent.",
            status_code=status.HTTP_200_OK,
        )


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Change User Password",
    )
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        temp_id = serializer.validated_data["hash"]
        password = serializer.validated_data["password"]

        cache_data = cache.get(temp_id)
        if not cache_data or not cache_data["is_valid"]:
            return Response(
                success=False,
                message="Reset password link is invalid or has expired",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        cache_data["is_valid"] = False
        email = cache_data["email"]
        cache.delete(temp_id)

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        name = user.name

        dynamic_values = {
            "first_name": name.split(" ")[0],
            "recipient": email,
        }

        tasks.send_reset_password_success_email.delay(email, dynamic_values)

        return Response(
            success=True,
            message="Password has been reset",
            status_code=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change User Password",
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()

        name = user.name
        email = user.email
        dynamic_values = {
            "first_name": name.split(" ")[0],
            "recipient": email,
        }

        tasks.send_reset_password_success_email.delay(email, dynamic_values)

        return Response(
            success=True,
            message="Password has been changed successfully",
            status_code=status.HTTP_200_OK,
        )
