from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers.user import UserSerializer
from utils.response import Response

User = get_user_model()


class UserProfile(GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve authenticated User",
    )
    def get(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = self.serializer_class(user)
        return Response(
            success=True,
            message="Profile retrieved successfully",
            status=status.HTTP_200_OK,
            data=serializer.data,
        )
