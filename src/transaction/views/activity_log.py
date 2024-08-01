from rest_framework import generics, status

from console.models.transaction import Transaction
from transaction.models import TransactionActivityLog
from transaction.serializers.activity_log import TransactionActivityLogSerializer
from utils.response import Response
from utils.transaction import get_transaction_instance


class TransactionActivityLogListView(generics.ListAPIView):
    serializer_class = TransactionActivityLogSerializer

    def list(self, request, transaction_id, *args, **kwargs):
        transaction = get_transaction_instance(transaction_id)
        if not transaction:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        qs = TransactionActivityLog.objects.filter(transaction=transaction).order_by(
            "created_at"
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(
            success=True,
            message="Transaction activity logs retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
