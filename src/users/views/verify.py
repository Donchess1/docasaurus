from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from core.resources.cache import Cache
from core.resources.email_service import EmailClient
from users import tasks
from users.serializers.verify_email import (VerifiedOTPPayloadSerializer,
                                            VerifyOTPSerializer)
from utils.response import Response
from utils.utils import GET_STARTED_BUYER_URL, GET_STARTED_SELLER_URL

User = get_user_model()
cache = Cache()


class VerifyOTPView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

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
                errors={
                    "detail": "OTP expired!",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if cache_data["otp"] != otp:
            return Response(
                success=False,
                errors={
                    "detail": "Invalid OTP!",
                },
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

        return Response(
            success=True,
            message="Email verified!",
            data={"email": email},
            status_code=status.HTTP_200_OK,
        )
