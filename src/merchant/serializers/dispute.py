from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from dispute import tasks
from merchant.utils import (
    get_merchant_escrow_users,
    transactions_delivery_date_has_not_elapsed,
)
from utils.utils import add_commas_to_transaction_amount, parse_date, parse_datetime

User = get_user_model()


class MerchantEscrowDisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = (
            "id",
            "transaction",
            "author",
            "buyer",
            "seller",
            "status",
            "priority",
            "reason",
            "description",
            "meta",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "transaction",
            "author",
            "meta",
            "buyer",
            "seller",
            "status",
            "created_at",
            "updated_at",
        )

    def validate(self, data):
        transaction = self.context.get("transaction")
        if Dispute.objects.filter(transaction=transaction).exists():
            raise serializers.ValidationError(
                {"transaction": "Dispute has already been raised for this transaction."}
            )
        if transactions_delivery_date_has_not_elapsed([str(transaction.id)]):
            raise serializers.ValidationError(
                {"transaction": "Delivery date is not due yet"}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        transaction = self.context.get("transaction")
        user = self.context.get("user")
        author = self.context.get("author")
        merchant = transaction.merchant
        priority = validated_data.get("priority")
        reason = validated_data.get("reason")
        description = validated_data.get("description")

        parties = get_merchant_escrow_users(transaction, merchant)
        buyer = parties.get("buyer", None)
        seller = parties.get("seller", None)

        escrow_meta = transaction.escrowmeta
        locked_amount = transaction.lockedamount

        dispute = Dispute.objects.create(
            buyer=buyer.customer.user,
            seller=seller.customer.user,
            author=author,
            status="PENDING",
            transaction=transaction,
            priority=priority,
            source="API",
            description=description,
            reason=reason,
        )

        dispute_author_is_seller = True if author == "SELLER" else False
        partner = (
            buyer.customer.user if dispute_author_is_seller else seller.customer.user
        )

        author_values = {
            "merchant_platform": merchant.name,
            "date": parse_datetime(dispute.created_at),
            "transaction_ref": transaction.reference,
            "item_name": transaction.meta.get("title"),
            "dispute_author_is_seller": dispute_author_is_seller,
            "partner_name": partner.name,
            "partner_email": partner.email,
            "dispute_reason": reason,
            "amount": f"NGN {add_commas_to_transaction_amount(str(transaction.amount))}",
            "delivery_date": parse_date(transaction.escrowmeta.delivery_date),
        }

        recipient_values = {
            "merchant_platform": merchant.name,
            "date": parse_datetime(dispute.created_at),
            "transaction_ref": transaction.reference,
            "item_name": transaction.meta.get("title"),
            "dispute_author_is_seller": dispute_author_is_seller,
            "partner_name": user.name,
            "partner_email": partner.email,
            "dispute_reason": reason,
            "amount": f"NGN {add_commas_to_transaction_amount(str(transaction.amount))}",
            "delivery_date": parse_date(transaction.escrowmeta.delivery_date),
        }

        tasks.send_dispute_raised_via_merchant_widget_author_email(
            user.email, author_values
        )
        tasks.send_dispute_raised_via_merchant_widget_receiver_email(
            partner.email, recipient_values
        )
        return dispute
