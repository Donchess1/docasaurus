import re

from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, permissions, status

from business.models.business import Business
from business.serializers.business import BusinessSerializer
from console.models.identity import NINIdentity
from console.serializers.identity import NINIdentitySerializer
from core.resources.cache import Cache
from core.resources.third_party.main import ThirdPartyAPI
from core.resources.upload_client import FileUploadClient
from users import tasks
from users.models.kyc import UserKYC
from users.models.profile import UserProfile
from users.serializers.kyc import UserKYCSerializer
from users.serializers.user import (
    OneTimeLoginCodeSerializer,
    UpdateKYCSerializer,
    UploadUserAvatarSerializer,
    UserSerializer,
)
from utils.kyc import create_user_kyc, kyc_meta_map
from utils.response import Response
from utils.utils import generate_otp, generate_temp_id

User = get_user_model()
cache = Cache()


class EditUserProfileView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user_id = request.user.id
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response(
                success=False,
                message=f"User does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        for field in request.data.keys():
            if field not in ["name", "phone"]:
                return Response(
                    success=False,
                    message="Only name and phone number can be updated",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        partial = True  # Allow partial updates
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        phone_number_update = request.data.get("phone")
        phone_pattern = re.compile(r"^020000000\d{2}$")
        if phone_number_update and phone_pattern.match(phone_number_update):
            return Response(
                success=False,
                message="Phone number is invalid.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if (
            phone_number_update
            and User.objects.filter(phone=phone_number_update).first()
        ):
            return Response(
                success=False,
                message="Phone number is already in use. Try another number",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        return Response(
            success=True,
            message="User updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class EditSellerBusinessProfileView(generics.GenericAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user_id = request.user.id
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response(
                success=False,
                message=f"User does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not user.is_seller:
            return Response(
                success=False,
                message="User cannot update business information",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        business = Business.objects.filter(user_id=user).first()
        if not business:
            return Response(
                success=False,
                message=f"Business does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        for field in request.data.keys():
            if field not in ["name", "phone", "description", "address"]:
                return Response(
                    success=False,
                    message="Only name, phone, description or address may be updated",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        partial = True  # Allow partial updates
        serializer = self.get_serializer(business, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        serializer.save()
        if request.data.get("phone"):
            user.phone = request.data["phone"]
            user.save()

        return Response(
            success=True,
            message="Business profile updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class UploadAvatarView(generics.GenericAPIView):
    serializer_class = UploadUserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    upload_client = FileUploadClient

    def post(self, request):
        user_id = request.user.id
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response(
                success=False,
                message=f"User does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        image = serializer.validated_data.get("image")
        obj = self.upload_client.execute(image)

        if not obj["success"]:
            return Response(**obj)

        avatar = obj["data"]["url"]
        try:
            profile = UserProfile.objects.get(user_id=user)
            profile.avatar = avatar
            profile.save()

        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="User Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            success=True,
            message="Avatar updated successfully",
            data=avatar,
            status_code=status.HTTP_200_OK,
        )


class UpdateKYCView(generics.GenericAPIView):
    serializer_class = UpdateKYCSerializer
    permission_classes = [permissions.IsAuthenticated]
    third_party = ThirdPartyAPI

    def put(self, request):
        user = request.user
        kyc = UserKYC.objects.filter(user_id=user).first()
        if kyc:
            return Response(
                success=False,
                message="KYC already exists",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        kyc_type = data.get("kyc_type")
        kyc_meta_id = data.get("kyc_meta_id")

        if not kyc_type in ("NIN"):
            return Response(
                success=False,
                message="Invalid or Disabled KYC Type",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        instance = NINIdentity.objects.filter(id=kyc_meta_id).first()
        if not instance:
            return Response(
                success=False,
                message="NIN Identity does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        obj = NINIdentitySerializer(instance)
        user_kyc = create_user_kyc(user, kyc_type, obj.data)
        user.userprofile.kyc_id = user_kyc
        user.userprofile.save()

        serializer = UserKYCSerializer(user_kyc)
        return Response(
            success=True,
            message="KYC updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class GenerateOneTimeLoginCodeView(generics.GenericAPIView):
    serializer_class = OneTimeLoginCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=serializer.errors.get("email")[0],
            )

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)
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
        cache.set(otp_key, value, 60 * 60 * 10)
        dynamic_values = {
            "name": name,
            "otp": otp,
            "recipient": email,
        }
        tasks.send_one_time_login_code_email(email, dynamic_values)

        return Response(
            success=True,
            message="Verification email sent!",
            data=payload,
            status_code=status.HTTP_201_CREATED,
        )
