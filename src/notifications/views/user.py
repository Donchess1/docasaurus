import math
import os
import uuid

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status, views
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

from notifications.models.notification import UserNotification
from notifications.serializers.notification import UserNotificationSerializer
from utils.pagination import CustomPagination
from utils.response import Response

User = get_user_model()


class UserNotificationListView(generics.ListAPIView):
    serializer_class = UserNotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["user", "category"]

    def get_queryset(self):
        user = self.request.user
        queryset = UserNotification.objects.filter(user=user).order_by("-created_at")
        return queryset

    @swagger_auto_schema(
        operation_description="List all notifications for an Authenticated User",
        responses={
            200: UserNotificationSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "User's notifcations retrieved successfully"
        response = self.get_paginated_response(serializer.data)
        return response


class UserNotificationDetailView(generics.GenericAPIView):
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get a notification by ID",
        responses={
            200: UserNotificationSerializer,
        },
    )
    def get(self, request, id, *args, **kwargs):
        instance = UserNotification.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="User Notification does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not instance.is_seen:
            instance.is_seen = True
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Notification retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )


# class NotificationDetailView(generics.GenericAPIView):
#     serializer_class = UserTransactionSerializer
#     permission_classes = (AllowAny,)

#     def get_queryset(self):
#         return Transaction.objects.all()

#     def get_transaction_instance(self, ref_or_id):
#         instance = self.get_queryset().filter(reference=ref_or_id).first()
#         if instance is None:
#             try:
#                 instance = self.get_queryset().filter(id=ref_or_id).first()
#             except Exception as e:
#                 instance = None
#         return instance

#     @swagger_auto_schema(
#         operation_description="Console: Get a transaction detail by ID or Reference",
#         responses={
#             200: UserTransactionSerializer,
#         },
#     )
#     def get(self, request, id, *args, **kwargs):
#         instance = self.get_transaction_instance(id)
#         if not instance:
#             return Response(
#                 success=False,
#                 message="Transaction does not exist",
#                 status_code=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = self.get_serializer(instance)
#         return Response(
#             success=True,
#             message="Transaction detail retrieved successfully.",
#             status_code=status.HTTP_200_OK,
#             data=serializer.data,
#         )
