from rest_framework import serializers


class FundWalletSerializer(serializers.Serializer):
    amount = serializers.IntegerField()


class FundWalletBankTransferPayloadSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    account_number = serializers.CharField()
    bank_name = serializers.CharField()
    account_expiration = serializers.CharField()
