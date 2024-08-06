from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers.profile import UserProfileSerializer
from users.services import get_user_profile_data
from utils.response import Response

User = get_user_model()


class UserProfileView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve Profile for Authenticated User",
    )
    def get(self, request):
        user: User = request.user
        data = get_user_profile_data(user)
        return Response(
            success=True,
            message="Profile retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=data,
        )


class EndUserTourGuideView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user: User = request.user
        user.userprofile.show_tour_guide = False
        user.userprofile.save()

        return Response(
            success=True,
            message="Tour guide status updated successfully",
            status_code=status.HTTP_200_OK,
        )
