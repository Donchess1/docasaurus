import re

from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from core.resources.jwt_client import JWTClient
from merchant.utils import get_merchant_by_email
from users.models.profile import UserProfile
from users.serializers.login import LoginPayloadSerializer, LoginSerializer
from users.serializers.user import UserSerializer
from utils.response import Response


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    jwt_client = JWTClient

    @swagger_auto_schema(
        operation_description="Login User",
        responses={
            200: LoginPayloadSerializer,
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(email=email, password=password)

        if not user:
            return Response(
                success=False,
                message="Invalid credentials. Try again",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_verified:
            return Response(
                success=False,
                message="Email not verified",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user_id = user.id

        profile = UserProfile.objects.get(user_id=user_id)
        profile.last_login_date = timezone.now()
        profile.save()

        # validate phone number - flag 02000000000 - 02000000099
        user_phone = user.phone
        phone_pattern = re.compile(r"^020000000\d{2}$")
        user.userprofile.phone_number_flagged = (
            True if phone_pattern.match(user_phone) else False
        )
        user.userprofile.save()

        token = self.jwt_client.sign(user_id)
        merchant = get_merchant_by_email(user.email)

        return Response(
            success=True,
            message="Login successful",
            data={
                "token": token["access_token"],
                "phone_number_flagged": user.userprofile.phone_number_flagged,
                "user": UserSerializer(user).data,
                "merchant": str(merchant.id) if merchant else None,
            },
            status_code=status.HTTP_200_OK,
        )
