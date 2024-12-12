from rest_framework import serializers


class BaseSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    total = serializers.IntegerField()


class StatusCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class VolumeCountSerializer(serializers.Serializer):
    volume = serializers.FloatField()
    count = serializers.IntegerField()


class BaseSystemMetricsSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    deposits = serializers.IntegerField()
    withdrawals = serializers.IntegerField()
    escrows = serializers.IntegerField()
    disputes = serializers.IntegerField()


class UserSystemMetricsSerializer(BaseSystemMetricsSerializer):
    product_purchases = serializers.IntegerField()
    product_settlements = serializers.IntegerField()
    merchant_settlements = serializers.IntegerField()


class MerchantSystemMetricsSerializer(BaseSystemMetricsSerializer):
    payout_configurations = serializers.IntegerField()
    merchant_settlements = serializers.IntegerField()
    customers = serializers.IntegerField()


class CustomerSystemMetricsSerializer(BaseSystemMetricsSerializer):
    pass
