from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, mixins, permissions, status, viewsets

from users.serializers.user import CheckUserByEmailViewSerializer, UserSerializer
from utils.pagination import CustomPagination
from utils.response import Response

User = get_user_model()


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination
    http_method_names = ["get", "post", "delete", "put"]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Users retrieved successfully"
        response = self.get_paginated_response(serializer.data)
        return response

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
        instance = self.get_object()
        for field in request.data.keys():
            if field not in ["name", "phone"]:
                return Response(
                    success=False,
                    message="Only name and phone number can be updated",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        partial = True  # Allow partial updates
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            success=True,
            message="User updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

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


class CheckUserByEmailView(generics.GenericAPIView):
    serializer_class = CheckUserByEmailViewSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Console: Check if user exists using email",
        responses={
            200: UserSerializer,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data.get("email")
        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(
                success=True,
                message="User found",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                success=False,
                message="User does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
