from django.contrib.auth import get_user_model
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import EscrowMeta, LockedAmount, Transaction

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
        if Dispute.objects.filter(transaction=value).exists():
            raise serializers.ValidationError(
                "A dispute has already been created for this transaction."
            )
        locked_amount = LockedAmount.objects.filter(transaction=value).first()
        if not locked_amount:
            raise serializers.ValidationError(
                "This transaction has not been locked yet"
            )

        seller = User.objects.filter(email=locked_amount.seller_email).first()
        if not seller:
            raise serializers.ValidationError("Seller does not exist")

        return value
