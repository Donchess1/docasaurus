from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets

from users.serializers.user import UserSerializer
from utils.response import Response

User = get_user_model()


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            success=True,
            message="Users fetched successfully",
            data=serializer.data,
            meta={"count": queryset.count()},
            status_code=status.HTTP_200_OK,
        )

    def retrieve(self, request, pk=None, *args, **kwargs):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response(
                success=False,
                message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(user)
        return Response(
            success=True,
            message="User fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def update(self, request, pk=None, *args, **kwargs):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response(
                success=False,
                message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            success=True,
            message="User updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response(
                success=False,
                message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.perform_destroy(instance)

        return Response(
            success=True,
            message="User deleted successfully",
            status_code=status.HTTP_200_OK,
        )
