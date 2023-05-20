from rest_framework import serializers


class FundWalletSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
