from django_filters import rest_framework as django_filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status

from console.models.transaction import Transaction
from transaction.filters import TransactionFilter
from transaction.permissions import IsAdminOrReadOnly
from transaction.serializers.user import UserTransactionSerializer
from utils.pagination import CustomPagination
from utils.response import Response


class TransactionListView(generics.ListAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = TransactionFilter
    search_fields = ["reference", "provider", "type"]
    ordering_fields = [
        "reference",
        "provider",
        "type",
        "status",
        "amount",
        "created_at",
    ]

    def get_queryset(self):
        return Transaction.objects.all().order_by("-created_at")

    @swagger_auto_schema(
        operation_description="List all the transaction in the DB",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            qs = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                qs,
                context={"hide_escrow_details": True, "hide_locked_amount": True},
                many=True,
            )
            self.pagination_class.message = "Transactions retrieved successfully."
            response = self.get_paginated_response(serializer.data)
            return response
        except Exception as e:
            return Response(
                success=False,
                message=f"{str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
