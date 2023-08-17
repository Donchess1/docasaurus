import uuid

from rest_framework import serializers

from console.models.transaction import EscrowMeta, Transaction
from utils.utils import generate_random_text, get_escrow_fees, validate_bank_account


class EscrowTransactionSerializer(serializers.Serializer):
    purpose = serializers.CharField()
    item_type = serializers.CharField(max_length=255)
    item_quantity = serializers.IntegerField()
    delivery_date = serializers.DateField()
    amount = serializers.IntegerField()
    bank_code = serializers.CharField(max_length=255)
    bank_account_number = serializers.CharField(max_length=10)
    partner_email = serializers.EmailField()

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
        }
        escrow_meta = EscrowMeta.objects.create(**escrow_meta_data)
        return transaction
