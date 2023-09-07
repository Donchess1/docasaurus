from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, permissions, status

from users.serializers.user import UserSerializer
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
