from rest_framework import serializers

from transaction.models import TransactionActivityLog


class TransactionActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionActivityLog
        fields = (
            "id",
            "transaction",
            "description",
            "meta",
            "created_at",
            "updated_at",
        )
