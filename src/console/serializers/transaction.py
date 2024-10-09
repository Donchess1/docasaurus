from rest_framework import serializers

from console.serializers.overview import BaseSummarySerializer, VolumeCountSerializer
from console.utils import TRANSACTION_CHART_STATUS


class DepositStatusSerializer(serializers.Serializer):
    PENDING = VolumeCountSerializer()
    SUCCESSFUL = VolumeCountSerializer()
    FAILED = VolumeCountSerializer()
    CANCELLED = VolumeCountSerializer()
    TOTAL = VolumeCountSerializer()


class WithdrawalStatusSerializer(serializers.Serializer):
    PENDING = VolumeCountSerializer()
    SUCCESSFUL = VolumeCountSerializer()
    FAILED = VolumeCountSerializer()
    TOTAL = VolumeCountSerializer()


class EscrowStatusSerializer(serializers.Serializer):
    PENDING = VolumeCountSerializer()
    SUCCESSFUL = VolumeCountSerializer()
    REJECTED = VolumeCountSerializer()
    FUFILLED = VolumeCountSerializer()
    REVOKED = VolumeCountSerializer()
    TOTAL = VolumeCountSerializer()


class SettlementStatusSerializer(serializers.Serializer):
    PENDING = VolumeCountSerializer()
    SUCCESSFUL = VolumeCountSerializer()
    FAILED = VolumeCountSerializer()
    TOTAL = VolumeCountSerializer()


class TransactionSummarySerializer(BaseSummarySerializer):
    currency = serializers.CharField()
    deposits = DepositStatusSerializer()
    withdrawals = WithdrawalStatusSerializer()
    escrows = EscrowStatusSerializer()
    settlements = SettlementStatusSerializer()
    merchant_settlements = SettlementStatusSerializer()
    product_settlements = SettlementStatusSerializer()
    product_purchases = SettlementStatusSerializer()


class TransactionChartSerializer(serializers.Serializer):
    currency = serializers.CharField()
    aggregate = serializers.CharField()
    period = serializers.CharField()
    transaction_status = serializers.ChoiceField(
        choices=TRANSACTION_CHART_STATUS, default="NGN"
    )
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    chart_data = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField())
    )


class TransactionEntitySchemaSerializer(serializers.Serializer):
    entity = serializers.CharField()
    type = serializers.ListField(child=serializers.CharField())
    mode = serializers.ListField(child=serializers.CharField())
    hierarchy_map = serializers.DictField()

class DisputeEntitySchemaSerializer(serializers.Serializer):
    entity = serializers.CharField()
    source = serializers.ListField(child=serializers.CharField())
    status = serializers.ListField(child=serializers.CharField())
    priority = serializers.ListField(child=serializers.CharField())
    author = serializers.ListField(child=serializers.CharField())
