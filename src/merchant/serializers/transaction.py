import os
from decimal import Decimal
from time import time

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.third_party.main import ThirdPartyAPI
from merchant.models import CustomerMerchant, Merchant, PayoutConfig
from merchant.utils import (
    escrow_user_is_valid,
    generate_deposit_transaction_for_escrow,
    get_customer_merchant_instance,
    get_merchant_active_payout_configuration,
    get_merchant_by_id,
    get_merchant_customer_transactions_by_customer_email,
    get_merchant_customers_by_user_type,
    get_merchant_customers_email_addresses,
    get_merchant_transaction_charges,
    transactions_are_already_unlocked,
    transactions_are_invalid_escrows,
    transactions_delivery_date_has_not_elapsed,
    unlock_customer_escrow_transaction_by_id,
    unlock_customer_escrow_transactions,
)
from transaction.serializers.locked_amount import LockedAmountSerializer
from transaction.services import get_escrow_transaction_parties_info
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.transaction import get_merchant_escrow_transaction_stakeholders
from utils.utils import (
    CURRENCIES,
    add_commas_to_transaction_amount,
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
            "buyer_consent_to_unlock",
            # "partner_email",
            # "delivery_tolerance",
            # "charge",
            # "created_at",
            # "updated_at",
        )

    def get_author_name(self, obj):
        return obj.transaction_id.user_id.name

    def get_parties(self, obj):
        # return obj.meta.get("parties", None)
        parties = get_escrow_transaction_parties_info(obj.transaction_id)
        return parties

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

    def __init__(self, *args, **kwargs):
        super(MerchantTransactionSerializer, self).__init__(*args, **kwargs)
        if self.context.get("hide_escrow_details"):
            self.fields.pop("escrow")

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
        data = serializer.data
        dispute = Dispute.objects.filter(transaction=obj).first()
        data["dispute_raised"] = True if dispute else False
        return data


class EscrowItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=["GOODS", "SERVICE"])
    item_quantity = serializers.IntegerField(min_value=1)
    delivery_date = serializers.DateField()
    amount = serializers.IntegerField()


class EscrowEntitySerializer(serializers.Serializer):
    seller = serializers.EmailField()
    items = EscrowItemSerializer(many=True)


class CreateMerchantEscrowTransactionSerializer(serializers.Serializer):
    buyer = serializers.EmailField()
    payout_configuration = serializers.PrimaryKeyRelatedField(
        queryset=PayoutConfig.objects.all(), required=False
    )
    currency = serializers.ChoiceField(choices=CURRENCIES, default="NGN")
    entities = EscrowEntitySerializer(many=True)

    def validate_payout_configuration(self, value):
        merchant = self.context.get("merchant")
        valid_config = PayoutConfig.objects.filter(
            id=str(value), merchant=merchant
        ).first()
        if not valid_config:
            raise serializers.ValidationError("Payout configuration does not exist.")
        return valid_config

    def validate_buyer(self, value):
        merchant = self.context.get("merchant")
        customer_list = get_merchant_customers_email_addresses(merchant)
        if not escrow_user_is_valid(value, customer_list):
            raise serializers.ValidationError(f"Buyer {value} does not exist.")
        return value

    def validate_seller(self, value, merchant):
        customer_list = get_merchant_customers_email_addresses(
            merchant,
        )
        return True if escrow_user_is_valid(value, customer_list) else False

    def validate_delivery_date(self, value):
        today = timezone.now().date()
        return False if value < today else True

    def validate_amount(self, value, title, currency):
        MINIMUM_AMOUNT = 500 if currency == "NGN" else 100
        if env == "test":
            MAXIMUM_AMOUNT = 5000 if currency == "NGN" else 1000
        else:  # live environment
            MAXIMUM_AMOUNT = float(
                "inf"
            )  # No cap on maximum amount in live environment

        if value < MINIMUM_AMOUNT:
            return (
                False,
                f"Minimum amount allowed in test mode is {currency} {add_commas_to_transaction_amount(MINIMUM_AMOUNT)}. Update <{title.upper()}>",
            )
        if value > MAXIMUM_AMOUNT:
            message = f"Maximum transaction amount allowed in test mode is {currency} {add_commas_to_transaction_amount(MAXIMUM_AMOUNT)}. Kindly update <{title.upper()}>"
            return (False, message)

        return True, "Valid amount"

    def validate_entities(self, entities):
        merchant = self.context.get("merchant")
        currency = self.initial_data.get("currency", "NGN")
        for entity in entities:
            seller_email = entity.get("seller")
            if not self.validate_seller(seller_email, merchant):
                raise serializers.ValidationError(
                    f"Seller <{seller_email}> does not exist."
                )
            for item in entity.get("items"):
                title = item.get("title")
                delivery_date = item.get("delivery_date")
                amount = item.get("amount")
                if not self.validate_delivery_date(delivery_date):
                    raise serializers.ValidationError(
                        f"Delivery date for {seller_email} to deliver <{title}> cannot be earlier than today."
                    )
                amount_is_valid, message = self.validate_amount(amount, title, currency)
                if not amount_is_valid:
                    raise serializers.ValidationError(message)
        return entities

    @transaction.atomic
    def create(self, validated_data):
        merchant = self.context.get("merchant")
        request_meta = self.context.get("request_meta")
        buyer = validated_data.get("buyer")
        entities = validated_data.get("entities")
        currency = validated_data.get("currency")
        payout_config = validated_data.get("payout_configuration", None)
        total_amount = 0
        for entity in entities:
            for item in entity["items"]:
                total_amount += int(item["amount"])
                item["delivery_date"] = str(item["delivery_date"])

        charge, amount_payable = get_escrow_fees(total_amount)
        merchant_payout_config = (
            get_merchant_active_payout_configuration(merchant)
            if not payout_config
            else payout_config
        )
        merchant_user_charges = get_merchant_transaction_charges(
            merchant, total_amount, merchant_payout_config
        )
        merchant_buyer_charge = merchant_user_charges.get("buyer_charge")
        merchant_seller_charge = merchant_user_charges.get("seller_charge")

        buyer_charge = charge
        payer = User.objects.filter(email=buyer).first()
        profile = payer.userprofile
        escrow_credits_used = False
        # Evaluating free escrow transactions
        buyer_free_escrow_credits = int(profile.free_escrow_transactions)
        if buyer_free_escrow_credits > 0:
            # reverse charges to buyer wallet & deplete free credits
            profile.free_escrow_transactions -= 1
            profile.save()
            buyer_charge = 0
            escrow_credits_used = True

        amount_to_charge = total_amount + buyer_charge + int(merchant_buyer_charge)
        tx_ref = generate_txn_reference()

        payment_breakdown = {
            "base_amount": str(total_amount),
            "buyer_escrow_fees": str(buyer_charge),
            "buyer_escrow_credits_used": escrow_credits_used,
            "seller_escrow_fees": str(charge),
            "buyer_merchant_fees": str(merchant_buyer_charge),
            "seller_merchant_fees": str(merchant_seller_charge),
            "total_merchant_fees": str(
                Decimal(str(merchant_buyer_charge))
                + Decimal(str(merchant_seller_charge))
            ),
            "total_payable": str(amount_to_charge),
            "currency": currency,
            "payout_configuration_name": merchant_payout_config.name,
            "payout_configuration_id": str(merchant_payout_config),
            "payment_reference": tx_ref,
        }

        meta = {
            "payment_breakdown": "payment_breakdown",
            "seller_escrow_breakdown": entities,
            "merchant": str(merchant.id),
            "payout_config": str(merchant_payout_config.id),
        }
        deposit_txn = generate_deposit_transaction_for_escrow(
            payer, amount_to_charge, tx_ref, meta, currency, merchant
        )

        buyer_customer_instance = get_customer_merchant_instance(buyer, merchant)
        description = f"Merchant {(merchant.name).upper()} initiated payment of {currency} {add_commas_to_transaction_amount(amount_to_charge)} for SENDER/BUYER {buyer_customer_instance.alternate_name} <{payer.email}> to fund escrow transaction."
        log_transaction_activity(deposit_txn, description, request_meta)

        flw_txn_data = {
            "tx_ref": tx_ref,
            "amount": amount_to_charge,
            "currency": currency,
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
                "action": "FUND_MERCHANT_ESCROW",
                "platform": "MERCHANT_API",
                "total_payable_amount": str(amount_to_charge),
            },
            "configurations": {
                "session_duration": 10,  # Session timeout in minutes (maxValue: 1440 minutes)
                "max_retry_attempt": 3,  # Max retry (int)
            },
        }
        return deposit_txn, flw_txn_data, payment_breakdown


class MerchantEscrowRedirectPayloadSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField()
    amount = serializers.IntegerField()
    redirect_url = serializers.URLField()


class UnlockCustomerEscrowTransactionByBuyerSerializer(serializers.Serializer):
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
        completed, message = unlock_customer_escrow_transactions(transactions, user)
        if not completed:
            raise serializers.ValidationError({"error": message})
        return completed, message


class InitiateCustomerWalletWithdrawalSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    currency = serializers.ChoiceField(choices=CURRENCIES)
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10, min_length=10)
    merchant_id = serializers.UUIDField()

    def validate(self, data):
        amount = data.get("amount")
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")
        merchant_id = data.get("merchant_id")
        currency = data.get("currency")
        user = self.context.get("user")

        merchant = get_merchant_by_id(merchant_id)
        if not merchant:
            raise serializers.ValidationError({"error": "Merchant does not exist"})
        charge, total_amount = get_withdrawal_fee(int(amount))
        status, message = user.validate_wallet_withdrawal_amount(total_amount, currency)
        if not status:
            raise serializers.ValidationError({"error": message})

        obj = ThirdPartyAPI.validate_bank_account(bank_code, account_number)
        if obj["status"] in ["error", False]:
            raise serializers.ValidationError({"error": "Invalid bank details"})
        data["merchant_platform"] = merchant.name
        data["merchant_id"] = str(merchant.id)
        data["amount"] = int(total_amount)
        return data


class InitiateCustomerWalletWithdrawalByMerchantSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.IntegerField()
    currency = serializers.ChoiceField(choices=CURRENCIES)
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10, min_length=10)

    def validate(self, data):
        amount = data.get("amount")
        email = data.get("email")
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")
        currency = data.get("currency")
        merchant = self.context.get("merchant")
        merchant_customer: CustomerMerchant = get_customer_merchant_instance(
            email, merchant
        )
        if not merchant_customer:
            raise serializers.ValidationError({"error": "Customer not found"})
        charge, total_amount = get_withdrawal_fee(int(amount))
        user = merchant_customer.customer.user
        status, message = user.validate_wallet_withdrawal_amount(total_amount, currency)
        if not status:
            raise serializers.ValidationError({"error": message})
        obj = ThirdPartyAPI.validate_bank_account(bank_code, account_number, currency)
        if obj["status"] in ["error", False]:
            raise serializers.ValidationError({"error": obj["message"]})
        data["merchant_platform"] = merchant.name
        data["merchant_id"] = str(merchant.id)
        data["amount"] = int(total_amount)
        return data


class ConfirmMerchantWalletWithdrawalSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    temp_id = serializers.CharField()


class MandateFundsReleaseSerializer(serializers.Serializer):
    buyer_email = serializers.EmailField()

    def validate_buyer_email(self, value):
        merchant = self.context.get("merchant")
        customer_list = get_merchant_customers_email_addresses(merchant)
        if not escrow_user_is_valid(value, customer_list):
            raise serializers.ValidationError(f"Buyer {value} does not exist.")
        return value


class ReleaseEscrowTransactionByMerchantSerializer(serializers.Serializer):
    pass
