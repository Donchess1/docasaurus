from django.db import transaction
from rest_framework import serializers

from core.resources.third_party.main import ThirdPartyAPI
from users.models.bank_account import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    bank_code = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=10, min_length=10)
    is_default = serializers.BooleanField(default=False)

    class Meta:
        model = BankAccount
        fields = (
            "id",
            "user_id",
            "bank_name",
            "bank_code",
            "account_name",
            "account_number",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "bank_name",
            "account_name",
            "user_id",
            "created_at",
            "updated_at",
        )

    def validate(self, data):
        user = self.context["request"].user
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")

        # we only allow 3 bank accounts per user
        if BankAccount.objects.filter(user_id=user).count() >= 3:
            raise serializers.ValidationError(
                {"bank": ["Maximum of 3 bank accounts allowed"]}
            )

        obj = ThirdPartyAPI.validate_bank_account(bank_code, account_number)
        if obj["status"] in ["error", False]:
            raise serializers.ValidationError(
                {"bank": ["Invalid bank account details"]}
            )

        # Check for duplicate bank account for the same user
        if BankAccount.objects.filter(
            user_id=user, bank_code=bank_code, account_number=account_number
        ).exists():
            raise serializers.ValidationError(
                {"bank": ["Bank account details already exists. Try another account"]}
            )

        banks = ThirdPartyAPI.list_banks()
        if not banks:
            raise serializers.ValidationError(
                {"bank": ["Error occurred while fetching banks"]}
            )
        bank_name = banks["banks_map"].get(bank_code)
        data["bank_name"] = bank_name
        data["account_name"] = obj["data"]["account_name"]

        # Ensure only one default account exists for the user
        if data.get("is_default"):
            BankAccount.objects.filter(user_id=user, is_default=True).update(
                is_default=False
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        bank_code = validated_data.get("bank_code")
        account_number = validated_data.get("account_number")
        bank_name = validated_data.get("bank_name")
        account_name = validated_data.get("account_name")
        is_default = validated_data.get("is_default", False)

        bank_account = BankAccount.objects.create(
            user_id=user,
            bank_name=bank_name,
            bank_code=bank_code,
            account_name=account_name,
            account_number=account_number,
            is_default=is_default,
        )
        return bank_account
