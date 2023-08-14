import os

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

from console import tasks
from console.models.transaction import Transaction
from transaction.serializers.user import UserTransactionSerializer
from users.models import UserProfile
from utils.html import generate_flw_payment_webhook_html
from utils.response import Response

User = get_user_model()


# class UserTransactionView(GenericAPIView):
#     serializer_class = UserTransactionSerializer
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Webhook for FLW Updates",
#     )
#     def get(self, request):
#         secret_hash = os.environ.get("FLW_SECRET_HASH")
#         verif_hash = request.headers.get("verif-hash", None)

#         if not verif_hash or verif_hash != secret_hash:
#             return Response(
#                 success=False,
#                 message="Invalid authorization token.",
#                 status_code=status.HTTP_403_FORBIDDEN,
#             )

#         serializer = self.serializer_class(data=request.data)
#         if not serializer.is_valid():
#             return Response(
#                 success=False,
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 errors=serializer.errors,
#             )

#         data = serializer.validated_data
#         event = data.get("event", None)
#         data = data.get("data", None)

#         html_content = generate_flw_payment_webhook_html(event, data)

#         amount_charged = data["amount"]
#         customer_email = data["customer"]["email"]

#         # LOG EVENT

#         # tracking webhook payload
#         dev_email = "devtosxn@gmail.com"
#         values = {
#             "webhook_html_content": html_content,
#         }
#         tasks.send_webhook_notification_email(dev_email, values)

#         if data["status"] == "failed":
#             return Response(
#                 success=True,
#                 message="Webhook processed successfully.",
#                 status_code=status.HTTP_200_OK,
#             )

#         try:
#             user = User.objects.get(email=customer_email)
#             profile = UserProfile.objects.get(user_id=user)
#             profile.wallet_balance += int(amount_charged)
#             profile.save()
#         except User.DoesNotExist:
#             return Response(
#                 success=False,
#                 message="User not found",
#                 status_code=status.HTTP_404_NOT_FOUND,
#             )
#         except UserProfile.DoesNotExist:
#             return Response(
#                 success=False,
#                 message="Profile not found",
#                 status_code=status.HTTP_404_NOT_FOUND,
#             )

#         return Response(
#             success=True,
#             message="Webhook processed successfully.",
#             status_code=status.HTTP_200_OK,
#         )


class CustomTransactionPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the transaction
        return obj.user_id == request.user.id


class UserTransactionListView(generics.ListAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = (IsAuthenticated, CustomTransactionPermission)
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "provider"]

    def get_queryset(self):
        return Transaction.objects.filter(user_id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response(
                success=True,
                message="Paginated transactions retrieved successfully.",
                status_code=status.HTTP_200_OK,
                data=response.data,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            success=True,
            message="Transactions retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
