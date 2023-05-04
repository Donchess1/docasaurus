from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from users.models.profile import UserProfile
from users.serializers.profile import UserProfileSerializer
from utils.response import Response

User = get_user_model()


class UserProfileView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve Profile for Authenticated User",
    )
    def get(self, request):
        user_id = request.user.id
        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(profile)
        return Response(
            success=True,
            message="Profile retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
