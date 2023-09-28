import uuid

from django.contrib.auth import get_user_model
from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.cache import Cache
from core.resources.third_party.main import ThirdPartyAPI
from utils.utils import generate_random_text, get_escrow_fees, validate_bank_account

User = get_user_model()
cache = Cache()


class EscrowTransactionSerializer(serializers.Serializer):
    purpose = serializers.CharField()
    item_type = serializers.CharField(max_length=255)
    item_quantity = serializers.IntegerField()
    delivery_date = serializers.DateField()
    amount = serializers.IntegerField()
    bank_code = serializers.CharField(max_length=255)
    bank_account_number = serializers.CharField(max_length=10)
    partner_email = serializers.EmailField()

    def validate_partner_email(self, value):
        request = self.context.get("request")
        if value == request.user.email:
            raise serializers.ValidationError(
                "Partner's email cannot be the same as your email"
            )
        return value

    def validate_bank_code(self, value):
        banks = cache.get("banks")
        if banks is None:
            banks = ThirdPartyAPI.list_banks()
            if banks["status"] == "error":
                raise serializers.ValidationError(
                    "Error occurred while retrieving list of banks"
                )
        bank_codes = [item["code"] for item in banks.get("sorted_banks")]
        if value not in bank_codes:
            raise serializers.ValidationError("Provide a valid bank code")
        return value

    def validate(self, data):
        bank_code = data.get("bank_code")
        bank_account_number = data.get("bank_account_number")

        banks = ThirdPartyAPI.list_banks()
        bank_name = banks["banks_map"].get(bank_code)

        obj = ThirdPartyAPI.validate_bank_account(bank_code, bank_account_number)
        if obj["status"] in ["error", False]:
            raise serializers.ValidationError(
                {"bank": ["Please provide valid bank account details"]}
            )

        data["bank_name"] = bank_name
        data["account_name"] = obj["data"]["accountName"]
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        author = "BUYER" if user.is_buyer else "SELLER"
        amount = validated_data.get("amount")
        purpose = validated_data.get("purpose")
        title = validated_data.get("item_type")
        charge, amount_payable = get_escrow_fees(amount)
        tx_ref = generate_random_text(length=12)

        transaction_data = {
            "user_id": user,
            "status": "PENDING",
            "type": "ESCROW",
            "provider": "MYBALANCE",
            "mode": "Web",
            "amount": amount,
            "charge": charge,
            "meta": {"title": title, "description": purpose},
            "reference": tx_ref,
            "provider_tx_reference": tx_ref,
        }
        transaction = Transaction.objects.create(**transaction_data)

        escrow_meta_data = {
            "author": "BUYER" if user.is_buyer else "SELLER",
            "transaction_id": transaction,
            "partner_email": validated_data.get("partner_email"),
            "purpose": validated_data.get("purpose"),
            "item_type": validated_data.get("item_type"),
            "item_quantity": validated_data.get("item_quantity"),
            "delivery_date": validated_data.get("delivery_date"),
            "delivery_tolerance": 3,
            "meta": {
                "bank_name": validated_data.get("bank_name"),
                "account_number": validated_data.get("bank_account_number"),
                "account_name": validated_data.get("account_name"),
            },
        }
        escrow_meta = EscrowMeta.objects.create(**escrow_meta_data)
        return transaction


class FundEscrowTransactionSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()
    amount_to_charge = serializers.IntegerField()

    def validate_transaction_reference(self, value):
        instance = Transaction.objects.filter(reference=value).first()
        if not instance:
            raise serializers.ValidationError("Transaction reference is not valid")
        if instance.type != "ESCROW":
            raise serializers.ValidationError(
                "Invalid transaction type. Must be ESCROW"
            )
        if instance.verified:
            raise serializers.ValidationError(
                "Transaction has been verified or paid for"
            )
        if instance.status == "REJECTED":
            raise serializers.ValidationError(
                "Unable to process payments for rejected escrow transaction"
            )
        # if instance.status != "APPROVED":
        #     raise serializers.ValidationError(
        #         "Transaction must be approved before payment"
        #     )
        if instance.status == "PENDING" and instance.escrowmeta.author == "SELLER":
            raise serializers.ValidationError(
                "Approve transaction before locking funds"
            )
        return value

    def validate_amount_to_charge(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount to charge must be greater than 0")
        return value

    def validate(self, data):
        user = self.context.get("user")
        transaction_reference = data.get("transaction_reference")
        amount_to_charge = data.get("amount_to_charge")
        transaction = Transaction.objects.get(reference=transaction_reference)

        deficit = (
            transaction.amount + transaction.charge
        ) - user.userprofile.wallet_balance

        if amount_to_charge < deficit:
            raise serializers.ValidationError(
                {
                    "amount_to_charge": [
                        "Amount to charge must be greater than or equal to the deficit"
                    ]
                }
            )

        return data


class EscrowTransactionPaymentSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()

    def validate_transaction_reference(self, value):
        instance = Transaction.objects.filter(reference=value).first()
        if not instance:
            raise serializers.ValidationError("Transaction reference is not valid")
        if instance.type != "ESCROW":
            raise serializers.ValidationError(
                "Invalid transaction type. Must be ESCROW"
            )
        if instance.verified:
            raise serializers.ValidationError(
                "Transaction has been verified or paid for"
            )
        if instance.status == "REJECTED":
            raise serializers.ValidationError(
                "Unable to process payments for rejected escrow transaction"
            )
        # if instance.status != "APPROVED":
        #     raise serializers.ValidationError(
        #         "Transaction must be approved before payment"
        #     )
        if instance.status == "PENDING" and instance.escrowmeta.author == "SELLER":
            raise serializers.ValidationError(
                "Approve transaction before locking funds"
            )
        return value


class UnlockEscrowTransactionSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()

    def validate_transaction_reference(self, value):
        instance = Transaction.objects.filter(reference=value).first()
        if not instance:
            raise serializers.ValidationError("Transaction reference is not valid")
        if instance.type != "ESCROW":
            raise serializers.ValidationError(
                "Invalid transaction type. Must be ESCROW"
            )
        if instance.status != "SUCCESSFUL":
            raise serializers.ValidationError(
                "Transaction must be paid for before unlocking"
            )
        obj = LockedAmount.objects.get(transaction=instance)
        if obj.status == "SETTLED":
            raise serializers.ValidationError(
                {"transaction": "Funds have already been unlocked to seller"}
            )
        seller_obj = User.objects.filter(
            email=obj.seller_email, is_verified=True
        ).first()
        if not seller_obj:
            raise serializers.ValidationError(
                {"seller": "Seller has not created or activated account on platform"}
            )
        return value
