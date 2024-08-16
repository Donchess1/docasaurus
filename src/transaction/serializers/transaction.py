import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.cache import Cache
from core.resources.third_party.main import ThirdPartyAPI
from utils.email import validate_email_address
from utils.utils import (
    PHONE_NUMBER_SERIALIZER_REGEX_NGN,
    SYSTEM_CURRENCIES,
    generate_txn_reference,
    get_escrow_fees,
)

User = get_user_model()
cache = Cache()


class EscrowTransactionSerializer(serializers.Serializer):
    purpose = serializers.CharField()
    item_type = serializers.CharField(max_length=255)
    item_quantity = serializers.IntegerField()
    delivery_date = serializers.DateField()
    amount = serializers.IntegerField()
    currency = serializers.ChoiceField(choices=SYSTEM_CURRENCIES, default="NGN")
    # bank_code = serializers.CharField(max_length=255)
    # bank_account_number = serializers.CharField(max_length=10)
    partner_email = serializers.EmailField()
    # partner_number = serializers.CharField(
    #     validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    # )

    def validate_partner_email(self, value):
        request = self.context.get("request")
        email = request.user.email
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        if value.lower() == email.lower():
            raise serializers.ValidationError(
                "You cannot lock an escrow using your own email"
            )
        return validated_response["normalized_email"].lower()

    # def validate_bank_code(self, value):
    #     banks = cache.get("banks")
    #     if banks is None:
    #         banks = ThirdPartyAPI.list_banks()
    #         if not banks:
    #             raise serializers.ValidationError(
    #                 "Error occurred while retrieving list of banks"
    #             )
    #     bank_codes = [item["code"] for item in banks.get("sorted_banks")]
    #     if value not in bank_codes:
    #         raise serializers.ValidationError("Invalid bank!")
    #     return value

    def validate(self, data):
        # bank_code = data.get("bank_code")
        # bank_account_number = data.get("bank_account_number")

        # banks = ThirdPartyAPI.list_banks()
        # if not banks:
        #     raise serializers.ValidationError(
        #         {"bank": ["Error fetching list of banks"]}
        #     )
        # bank_name = banks["banks_map"].get(bank_code)

        # obj = ThirdPartyAPI.validate_bank_account(bank_code, bank_account_number)
        # if obj["status"] in ["error", False]:
        #     raise serializers.ValidationError({"bank": [obj["message"]]})
        # data["bank_name"] = bank_name
        # data["account_name"] = obj["data"]["account_name"]

        # Validate delivery date
        delivery_date = data.get("delivery_date")
        today = timezone.now().date()
        if delivery_date < today:
            raise serializers.ValidationError(
                {"delivery_date": "You cannot set a date in the past."}
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        author = "BUYER" if user.is_buyer else "SELLER"
        amount = validated_data.get("amount")
        currency = validated_data.get("currency")
        purpose = validated_data.get("purpose")
        title = validated_data.get("item_type")
        charge, amount_payable = get_escrow_fees(amount)
        tx_ref = generate_txn_reference()

        transaction_data = {
            "user_id": user,
            "status": "PENDING",
            "type": "ESCROW",
            "provider": "MYBALANCE",
            "mode": "WEB",
            "currency": currency,
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
                "bank_name": validated_data.get("bank_name", ""),
                "account_number": validated_data.get("bank_account_number", ""),
                "account_name": validated_data.get("account_name", ""),
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
            raise serializers.ValidationError("Invalid transaction reference")
        if instance.type != "ESCROW":
            raise serializers.ValidationError("Invalid escrow transaction")
        if instance.verified:
            raise serializers.ValidationError(
                "Transaction has been verified or paid for"
            )
        if instance.status == "REJECTED":
            raise serializers.ValidationError(
                "You cannot lock funds for a rejected escrow transaction"
            )
        # if instance.status != "APPROVED":
        #     raise serializers.ValidationError(
        #         "Transaction must be approved before payment"
        #     )
        if (
            instance.meta.get("escrow_action") != "APPROVED"
            and instance.escrowmeta.author == "SELLER"
        ):
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
        profile = user.userprofile
        transaction_reference = data.get("transaction_reference")
        amount_to_charge = data.get("amount_to_charge")
        transaction = Transaction.objects.get(reference=transaction_reference)

        # Evaluating free escrow transactions
        buyer_free_escrow_credits = int(profile.free_escrow_transactions)
        amount_payable = transaction.amount + transaction.charge
        if buyer_free_escrow_credits > 0:
            # deplete free credits and make transaction free
            profile.free_escrow_transactions -= 1
            profile.save()
            amount_payable = transaction.amount

        status, resource = user.get_currency_wallet(transaction.currency)
        if not status:
            raise serializers.ValidationError({"wallet": [resource]})
        wallet = resource
        deficit = amount_payable - wallet.balance

        if amount_to_charge < deficit:
            raise serializers.ValidationError(
                {
                    "amount_to_charge": [
                        f"Minimum amount to fund is {transaction.currency} {deficit}"
                    ]
                }
            )

        return data


class EscrowTransactionPaymentSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()

    def validate_transaction_reference(self, value):
        instance = Transaction.objects.filter(reference=value).first()
        if not instance:
            raise serializers.ValidationError("Invalid transaction reference")
        if instance.type != "ESCROW":
            raise serializers.ValidationError("Invalid escrow transaction")
        if instance.verified:
            raise serializers.ValidationError(
                "Transaction has been verified or paid for"
            )
        if instance.status == "REJECTED":
            raise serializers.ValidationError(
                "You cannot lock funds for a rejected escrow transaction"
            )
        # if instance.status != "APPROVED":
        #     raise serializers.ValidationError(
        #         "Transaction must be approved before payment"
        #     )
        if (
            instance.meta.get("escrow_action") != "APPROVED"
            and instance.escrowmeta.author == "SELLER"
        ):
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
        if instance.status == "FUFILLED":
            raise serializers.ValidationError("Funds have already been unlocked")
        if instance.status == "REJECTED":
            raise serializers.ValidationError("Transaction was rejected")
        if instance.status != "SUCCESSFUL":
            raise serializers.ValidationError(
                "Transaction must be paid for before unlocking"
            )
        if not instance.meta.get("escrow_action"):
            raise serializers.ValidationError(
                "Transaction is yet to be approved or rejected"
            )
        obj = LockedAmount.objects.filter(transaction=instance).first()
        if not obj:
            raise serializers.ValidationError("Funds have not been locked")
        if obj.status == "SETTLED":
            raise serializers.ValidationError(
                "Funds have already been unlocked to seller"
            )
        seller_obj = User.objects.filter(
            email=obj.seller_email, is_verified=True
        ).first()
        if not seller_obj:
            raise serializers.ValidationError(
                {"seller": "Seller has not created or activated account on platform"}
            )
        return value
