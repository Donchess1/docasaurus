import os

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from merchant.utils import (
    check_escrow_user_is_valid,
    check_transactions_already_unlocked,
    check_transactions_are_valid_escrows,
    check_transactions_delivery_date_has_elapsed,
    create_merchant_escrow_transaction,
    generate_deposit_transaction_for_escrow,
    get_merchant_customer_transactions_by_customer_email,
    get_merchant_customers_by_user_type,
    unlock_customer_escrow_transactions,
)
from transaction.serializers.locked_amount import LockedAmountSerializer
from utils.utils import generate_random_text, generate_txn_reference, get_escrow_fees

User = get_user_model()
MERCHANT_REDIRECT_BASE_URL = os.environ.get("MERCHANT_REDIRECT_BASE_URL", "")


class EscrowTransactionMetaSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = EscrowMeta
        fields = (
            "id",
            "author",
            "author_name",
            "purpose",
            "item_type",
            "item_quantity",
            "delivery_date",
            "meta",
            # "partner_email",
            # "delivery_tolerance",
            # "charge",
            # "created_at",
            # "updated_at",
        )

    def get_author_name(self, obj):
        return obj.transaction_id.user_id.name


class MerchantTransactionSerializer(serializers.ModelSerializer):
    # locked_amount = serializers.SerializerMethodField()
    escrow = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id",
            "user_id",
            "status",
            "type",
            "mode",
            "reference",
            "narration",
            "amount",
            "charge",
            "remitted_amount",
            "currency",
            "provider",
            "provider_tx_reference",
            "meta",
            "merchant",
            "verified",
            # "locked_amount",
            "escrow",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "provider_tx_reference",
            "meta",
            "merchant",
            "verified",
            "user_id",
            "type",
            "mode",
            "reference",
            "narration",
            "amount",
            "charge",
            "remitted_amount",
            "currency",
            "locked_amount",
            "escrow",
            "provider",
        )

    def get_locked_amount(self, obj):
        instance = LockedAmount.objects.filter(transaction=obj).first()
        if not instance:
            return None
        serializer = LockedAmountSerializer(instance=instance)
        return serializer.data

    def get_escrow(self, obj):
        instance = EscrowMeta.objects.filter(transaction_id=obj).first()
        if not instance:
            return None
        serializer = EscrowTransactionMetaSerializer(instance=instance)
        return serializer.data


class CreateMerchantEscrowTransactionSerializer(serializers.Serializer):
    purpose = serializers.CharField()
    item_type = serializers.CharField(max_length=255)
    item_quantity = serializers.IntegerField()
    delivery_date = serializers.DateField()
    amount = serializers.IntegerField()
    buyer = serializers.EmailField()
    seller = serializers.EmailField()

    def validate_buyer(self, value):
        merchant = self.context.get("merchant")
        user_list = get_merchant_customers_by_user_type(merchant, "BUYER")
        if not check_escrow_user_is_valid(value, user_list):
            raise serializers.ValidationError("Buyer does not exist.")
        return value

    def validate_seller(self, value):
        merchant = self.context.get("merchant")
        user_list = get_merchant_customers_by_user_type(merchant, "SELLER")
        if not check_escrow_user_is_valid(value, user_list):
            raise serializers.ValidationError("Seller does not exist.")
        return value

    def validate_delivery_date(self, value):
        today = timezone.now().date()
        if value < today:
            raise serializers.ValidationError(
                "Delivery date cannot be earlier that today."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        merchant = self.context.get("merchant")
        amount = validated_data.get("amount")
        purpose = validated_data.get("purpose")
        title = validated_data.get("item_type")
        item_type = validated_data.get("item_type")
        item_quantity = validated_data.get("item_quantity")
        delivery_date = validated_data.get("delivery_date")
        buyer = validated_data.get("buyer")
        seller = validated_data.get("seller")
        charge, amount_payable = get_escrow_fees(amount)
        tx_ref = generate_random_text(length=20)

        escrow_txn_instance = create_merchant_escrow_transaction(
            merchant,
            buyer,
            seller,
            charge,
            amount,
            purpose,
            title,
            tx_ref,
            item_type,
            item_quantity,
            delivery_date,
        )

        payer = User.objects.filter(email=buyer).first()
        amount_to_charge = amount + charge
        new_tx_ref = generate_txn_reference()
        deposit_txn = generate_deposit_transaction_for_escrow(
            escrow_txn_instance, payer, amount_to_charge, new_tx_ref
        )

        flw_txn_data = {
            "tx_ref": new_tx_ref,
            "amount": amount_to_charge,
            "currency": "NGN",
            "redirect_url": f"{MERCHANT_REDIRECT_BASE_URL}",
            "customer": {
                "email": payer.email,
                "phone_number": payer.phone,
                "name": payer.name,
            },
            "customizations": {
                "title": "MyBalance",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            },
            "meta": {
                "escrow_transaction_reference": escrow_txn_instance.reference,
            },
        }
        return flw_txn_data


class MerchantEscrowRedirectPayloadSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()
    amount = serializers.IntegerField()
    redirect_url = serializers.URLField()


class UnlockMerchantEscrowTransactionSerializer(serializers.Serializer):
    transactions = serializers.ListField(child=serializers.UUIDField())

    def validate(self, data):
        transactions = data.get("transactions")
        merchant = self.context.get("merchant")
        user = self.context.get("user")

        valid_customer_transactions = (
            get_merchant_customer_transactions_by_customer_email(user.email, merchant)
        )
        valid_customer_transactions_ids = [
            transaction.id for transaction in valid_customer_transactions
        ]

        if not set(transactions).issubset(set(valid_customer_transactions_ids)):
            raise serializers.ValidationError(
                {"transactions": "One or more invalid transaction(s) to be unlocked"}
            )

        transactions = list(set(transactions))

        if not check_transactions_are_valid_escrows(transactions):
            raise serializers.ValidationError(
                {"transactions": "One or more transaction(s) not a valid escrow"}
            )

        if check_transactions_delivery_date_has_elapsed(transactions):
            raise serializers.ValidationError(
                {"transactions": "One or more transaction(s) not due for unlocking yet"}
            )

        if not check_transactions_already_unlocked(transactions):
            raise serializers.ValidationError(
                {
                    "transactions": "One or more transaction(s) have already been unlocked"
                }
            )
        data["transactions"] = transactions
        return data

    @transaction.atomic
    def create(self, validated_data):
        transactions = validated_data.get("transactions")
        user = self.context.get("user")
        res = unlock_customer_escrow_transactions(transactions, user)
        print("UNLOCKING RES", res)
        return res
