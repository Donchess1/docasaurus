from rest_framework import serializers

from utils.utils import CURRENCIES


class WalletAmountSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    currency = serializers.ChoiceField(
        choices=CURRENCIES, default="NGN", required=False
    )


class FundWalletBankTransferPayloadSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    account_number = serializers.CharField()
    bank_name = serializers.CharField()
    account_expiration = serializers.CharField()


class WalletWithdrawalAmountSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    currency = serializers.ChoiceField(
        choices=CURRENCIES, default="NGN", required=False
    )
    description = serializers.CharField(required=False)
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10, min_length=10)
