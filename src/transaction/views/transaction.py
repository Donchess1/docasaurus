from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny

from console.models.transaction import Transaction
from transaction.pagination import LargeResultsSetPagination
from transaction.serializers.user import UserTransactionSerializer
from utils.response import Response


class TransactionListView(generics.ListAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = (AllowAny,)
    pagination_class = LargeResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "provider", "type"]

    def get_queryset(self):
        return Transaction.objects.all().order_by("-created_at")

    @swagger_auto_schema(
        operation_description="List all the transaction in the Database",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)

        serializer = self.get_serializer(qs, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response(
            success=True,
            message="All transactions retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=response.data,
        )
