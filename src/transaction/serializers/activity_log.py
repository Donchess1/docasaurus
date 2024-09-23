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


class TransactionActivityLogResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    reference = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    logs = TransactionActivityLogSerializer(many=True)
