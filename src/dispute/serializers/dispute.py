from django.contrib.auth import get_user_model
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from merchant.utils import check_transactions_delivery_date_has_elapsed

User = get_user_model()


class DisputeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "is_verified",
            "created_at",
            "updated_at",
        )


class DisputeTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "status",
            "type",
            "reference",
            "amount",
            "charge",
            "created_at",
            "updated_at",
        )


class DisputeSerializer(serializers.ModelSerializer):
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
            "author",
            "buyer",
            "seller",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_transaction(self, value):
        if check_transactions_delivery_date_has_elapsed([str(value.id)]):
            raise serializers.ValidationError("Delivery date is not due yet")
        if Dispute.objects.filter(transaction=value).exists():
            raise serializers.ValidationError(
                "A dispute has already been created for this transaction."
            )
        escrow_action = value.meta.get("escrow_action")
        if not escrow_action:
            raise serializers.ValidationError(
                "Transaction is yet to be approved or rejected"
            )
        elif escrow_action == "REJECTED":
            raise serializers.ValidationError("Transaction was already rejected")

        locked_amount = LockedAmount.objects.filter(transaction=value).first()
        if not locked_amount:
            raise serializers.ValidationError("Escrow funds have not been locked yet")

        seller = User.objects.filter(email=locked_amount.seller_email).first()
        if not seller:
            raise serializers.ValidationError("Seller does not exist on the platform")
        if value.escrowmeta.author == "SELLER":
            buyer = User.objects.filter(email=value.escrowmeta.partner_email).first()
            if not buyer:
                raise serializers.ValidationError(
                    "Buyer does not exist on the platform"
                )

        return value


class ResolveDisputeSerializer(serializers.Serializer):
    destination = serializers.ChoiceField(choices=("BUYER", "SELLER"))
