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


class TransactionChartSerializer(serializers.Serializer):
    currency = serializers.CharField()
    aggregate = serializers.CharField()
    period = serializers.CharField()
    transaction_status = serializers.ChoiceField(
        choices=TRANSACTION_CHART_STATUS, default="NGN")
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    chart_data = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField())
    )
