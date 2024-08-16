from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, QuerySet
from django_filters import rest_framework as django_filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from console.filters import UserFilter
from console.models.transaction import Transaction
from console.permissions import IsSuperAdmin
from console.serializers.base import ConsoleUserWalletSerializer
from console.serializers.overview import UserSystemMetricsSerializer
from console.utils import get_user_system_metrics
from users.models.profile import UserProfile
from users.models.wallet import Wallet
from users.serializers.profile import UserProfileSerializer
from users.serializers.user import (
    CheckUserByEmailViewSerializer,
    CheckUserByPhoneNumberViewSerializer,
    UserSerializer,
)
from users.services import get_user_profile_data
from utils.pagination import CustomPagination
from utils.response import Response
from utils.utils import REGISTRATION_REFERRER

User = get_user_model()


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().exclude(is_admin=True).order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination
    http_method_names = ["get", "patch"]
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = UserFilter
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["name", "email", "phone", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserProfileSerializer
        elif self.action == "get_user_wallets":
            return ConsoleUserWalletSerializer
        elif self.action == "get_user_system_metrics":
            return UserSystemMetricsSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            filtered_queryset = self.filter_queryset(queryset)
            qs = self.paginate_queryset(filtered_queryset)
            serializer = self.get_serializer(qs, many=True)
            self.pagination_class.message = "Users retrieved successfully"
            response = self.get_paginated_response(serializer.data)
            return response

        except DjangoValidationError as e:
            return Response(
                success=False,
                message=f"{str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except DRFValidationError as e:
            return Response(
                success=False,
                message=f"{e.detail}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                success=False,
                message=f"Unexpected error occurred. {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def retrieve(self, request, pk=None, *args, **kwargs):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response(
                success=False,
                message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        data = get_user_profile_data(user)
        return Response(
            success=True,
            message="User fetched successfully",
            data=data,
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
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
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
        instance.delete()

        return Response(
            success=True,
            message="User deleted successfully",
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdmin])
    def flag(self, request, pk=None):
        user = self.get_object()
        user.flag_account()
        return Response(
            success=True,
            message="User flagged successfully",
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdmin])
    def unflag(self, request, pk=None):
        user = self.get_object()
        user.unflag_account()
        return Response(
            success=True,
            message="User unflagged successfully",
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdmin])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.deactivate_account()
        return Response(
            success=True,
            message="User deactivated successfully",
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdmin])
    def reactivate(self, request, pk=None):
        user = self.get_object()
        user.reactivate_account()
        return Response(
            success=True,
            message="User reactivated successfully",
            status_code=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsSuperAdmin],
        url_path="wallets",
        serializer_class=ConsoleUserWalletSerializer,
    )
    def get_user_wallets(self, request, pk=None):
        user = self.get_object()
        wallets = Wallet.objects.filter(user=user).order_by(
            "-currency"
        )  # ["USD", "NGN"]
        serializer = self.serializer_class(wallets, many=True)
        return Response(
            success=True,
            message="User Wallets Info retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsSuperAdmin],
        url_path="system-metrics",
        serializer_class=UserSystemMetricsSerializer,
    )
    def get_user_system_metrics(self, request, pk=None):
        user = self.get_object()
        metrics_data = get_user_system_metrics(user)
        serializer = self.serializer_class(metrics_data)
        return Response(
            success=True,
            message="User metrics retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class UserRegistrationMetricsView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Metrics: Get referrer counts",
        responses={
            200: None,
        },
    )
    def get(self, request):
        referrer_counts = UserProfile.objects.values("referrer").annotate(
            count=Count("referrer")
        )

        # Initialize dictionary with zero counts for each referrer type
        referrer_metrics = {key: 0 for key in REGISTRATION_REFERRER}

        for item in referrer_counts:
            referrer_metrics[item["referrer"]] = item["count"]

        return Response(
            success=True,
            message="Referrer counts retrieved successfully",
            data=referrer_metrics,
            status_code=status.HTTP_200_OK,
        )


class CheckUserWalletInfoByEmailView(generics.GenericAPIView):
    serializer_class = CheckUserByEmailViewSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Console: Check User Wallet Info",
        responses={
            200: ConsoleUserWalletSerializer,
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
            wallets = Wallet.objects.filter(user=user).order_by(
                "-currency"
            )  # ["USD", "NGN"]
            serializer = ConsoleUserWalletSerializer(wallets, many=True)
            return Response(
                success=True,
                message=f"Wallet Info retrieved successfully for '{email}'",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                success=False,
                message="User does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
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


class CheckUserByPhoneView(generics.GenericAPIView):
    serializer_class = CheckUserByPhoneNumberViewSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Console: Check if user exists using phone number",
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

        phone = serializer.validated_data.get("phone")
        try:
            user = User.objects.get(phone=phone)
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
