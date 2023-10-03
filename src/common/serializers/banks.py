from rest_framework import serializers

from users.models.bank_account import BankAccount


class BankListSerializer(serializers.Serializer):
    name = serializers.CharField()
    # slug = serializers.CharField()
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


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            "id",
            "user_id",
            "bank_name",
            "bank_code",
            "account_name",
            "account_number",
            "is_active",
            "created_at",
            "updated_at",
        )
