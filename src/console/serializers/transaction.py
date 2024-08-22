from rest_framework import serializers

from console.serializers.overview import BaseSummarySerializer, VolumeCountSerializer


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
