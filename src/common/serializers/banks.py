from rest_framework import serializers


class BankListSerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.CharField()
    code = serializers.CharField()


class ValidateBankAccountSerializer(serializers.Serializer):
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10)


class BankAccountPayloadSerializer(serializers.Serializer):
    nuban = serializers.CharField()
    account_name = serializers.CharField()
    identity_type = serializers.CharField()
    bank = serializers.CharField()
    account_currency = serializers.CharField()
