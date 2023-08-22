from rest_framework import serializers

from users.models.bank_account import BankAccount


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
