from rest_framework import generics, status

from console.models.transaction import Transaction
from console.permissions import IsSuperAdmin
from transaction.models import TransactionActivityLog
from transaction.serializers.activity_log import TransactionActivityLogSerializer
from utils.response import Response
from utils.transaction import get_transaction_instance


class TransactionActivityLogListView(generics.ListAPIView):
    serializer_class = TransactionActivityLogSerializer
    permission_classes = (IsSuperAdmin,)

    def list(self, request, id, *args, **kwargs):
        transaction = get_transaction_instance(id)
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
        data = {
            "id": transaction.id,
            "reference": transaction.reference,
            "type": transaction.type,
            "status": transaction.status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "logs": serializer.data,
        }
        return Response(
            success=True,
            message="Transaction activity logs retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=data,
        )
