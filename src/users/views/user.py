from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, permissions, status

from core.resources.upload_client import FileUploadClient
from users.models.profile import UserProfile
from users.serializers.user import UploadUserAvatarSerializer, UserSerializer
from utils.response import Response

User = get_user_model()


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
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            success=True,
            message="User updated successfully",
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
