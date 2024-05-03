import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.third_party.main import ThirdPartyAPI
from merchant.utils import (
    create_merchant_escrow_transaction,
    escrow_user_is_valid,
    generate_deposit_transaction_for_escrow,
    get_merchant_active_payout_configuration,
    get_merchant_by_id,
    get_merchant_customer_transactions_by_customer_email,
    get_merchant_customers_by_user_type,
    get_merchant_transaction_charges,
    transactions_are_already_unlocked,
    transactions_are_invalid_escrows,
    transactions_delivery_date_has_not_elapsed,
    unlock_customer_escrow_transactions,
)
from transaction.serializers.locked_amount import LockedAmountSerializer
from utils.utils import (
    generate_random_text,
    generate_txn_reference,
    get_escrow_fees,
    get_withdrawal_fee,
)

User = get_user_model()
MERCHANT_REDIRECT_BASE_URL = os.environ.get("MERCHANT_REDIRECT_BASE_URL", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class EscrowTransactionMetaSerializer(serializers.ModelSerializer):
    # author_name = serializers.SerializerMethodField()
    parties = serializers.SerializerMethodField()
    payment_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = EscrowMeta
        fields = (
            # "id",
            # "author",
            # "author_name",
            # "purpose",
            # "item_type",
            "item_quantity",
            "delivery_date",
            # "meta",
            "parties",
            "payment_breakdown",
            # "partner_email",
            # "delivery_tolerance",
            # "charge",
            # "created_at",
            # "updated_at",
        )

    def get_author_name(self, obj):
        return obj.transaction_id.user_id.name

    def get_parties(self, obj):
        return obj.meta.get("parties", None)

    def get_payment_breakdown(self, obj):
        return obj.meta.get("payment_breakdown", None)


class MerchantTransactionSerializer(serializers.ModelSerializer):
    # locked_amount = serializers.SerializerMethodField()
    escrow = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id",
            # "user_id",
            "status",
            "type",
            "mode",
            "reference",
            # "narration",
            "amount",
            "charge",
            # "remitted_amount",
            "currency",
            # "provider",
            # "provider_tx_reference",
            "meta",
            # "merchant",
            "verified",
            # "locked_amount",
            "escrow",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            # "provider_tx_reference",
            "meta",
            # "merchant",
            "verified",
            # "user_id",
            "type",
            "mode",
            "reference",
            # "narration",
            "amount",
            "charge",
            # "remitted_amount",
            "currency",
            # "locked_amount",
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
        if not escrow_user_is_valid(value, user_list):
            raise serializers.ValidationError("Buyer does not exist.")
        return value

    def validate_seller(self, value):
        merchant = self.context.get("merchant")
        user_list = get_merchant_customers_by_user_type(merchant, "SELLER")
        if not escrow_user_is_valid(value, user_list):
            raise serializers.ValidationError("Seller does not exist.")
        return value

    def validate_delivery_date(self, value):
        today = timezone.now().date()
        if value < today:
            raise serializers.ValidationError(
                "Delivery date cannot be earlier that today."
            )
        return value

    def validate_amount(self, value):
        if env == "test" and value > 30000:
            raise serializers.ValidationError("Use amounts less than NGN30,000")
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

        merchant_payout_config = get_merchant_active_payout_configuration(merchant)
        merchant_user_charges = get_merchant_transaction_charges(
            merchant, amount, merchant_payout_config
        )
        merchant_buyer_charge = merchant_user_charges.get("buyer_charge")
        merchant_seller_charge = merchant_user_charges.get("seller_charge")
        escrow_txn_instance, escrow_txn_meta = create_merchant_escrow_transaction(
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
            merchant_payout_config,
        )

        payer = User.objects.filter(email=buyer).first()
        amount_to_charge = amount + charge + int(merchant_buyer_charge)

        payment_breakdown = {
            "base_amount": str(amount),
            "buyer_escrow_fees": str(charge),
            "seller_escrow_fees": str(charge),
            "buyer_merchant_fees": str(merchant_buyer_charge),
            "seller_merchant_fees": str(merchant_seller_charge),
            "total_merchant_fees": str(
                Decimal(str(merchant_buyer_charge))
                + Decimal(str(merchant_seller_charge))
            ),
            "total_payable": str(amount_to_charge),
            "currency": "NGN",
        }
        escrow_txn_meta.meta.update({"payment_breakdown": payment_breakdown})
        escrow_txn_meta.save()
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
                "total_payable_amount": str(amount_to_charge),
            },
        }
        return flw_txn_data, payment_breakdown


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
                {"error": "One or more transaction(s) invalid for user"}
            )

        transactions = list(set(transactions))

        if transactions_are_invalid_escrows(transactions):
            raise serializers.ValidationError(
                {"error": "One or more transaction(s) not a valid escrow"}
            )

        if transactions_delivery_date_has_not_elapsed(transactions):
            raise serializers.ValidationError(
                {"error": "One or more transaction(s) not due for unlocking yet"}
            )

        if transactions_are_already_unlocked(transactions):
            raise serializers.ValidationError(
                {"error": "One or more transaction(s) have already been unlocked"}
            )
        data["transactions"] = transactions
        return data

    @transaction.atomic
    def create(self, validated_data):
        transactions = validated_data.get("transactions")
        user = self.context.get("user")
        completed = unlock_customer_escrow_transactions(transactions, user)
        if not completed:
            raise serializers.ValidationError(
                {"error": "One or more transaction(s) could not be unlocked"}
            )
        return transactions


class InitiateMerchantWalletWithdrawalSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10, min_length=10)
    merchant_id = serializers.UUIDField()

    def validate(self, data):
        amount = data.get("amount")
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")
        merchant_id = data.get("merchant_id")
        user = self.context.get("user")

        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            raise serializers.ValidationError({"error": "Merchant does not exist"})
        charge, total_amount = get_withdrawal_fee(int(amount))
        if total_amount > user.userprofile.wallet_balance:
            raise serializers.ValidationError({"error": "Insufficient funds"})

        obj = ThirdPartyAPI.validate_bank_account(bank_code, account_number)
        if obj["status"] in ["error", False]:
            raise serializers.ValidationError({"error": "Invalid bank details"})
        data["merchant_platform"] = merchant.name
        data["merchant_id"] = str(merchant.id)
        data["amount"] = int(total_amount)
        return data


class ConfirmMerchantWalletWithdrawalSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    temp_id = serializers.CharField()
