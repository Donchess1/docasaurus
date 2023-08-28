from django.contrib.auth import get_user_model
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import LockedAmount, Transaction

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
            raise serializers.ValidationError("User does not exist")

        return value

    def create(self, validated_data):
        user = self.context.get("user")
        transaction = validated_data.pop("transaction")
        locked_amount = LockedAmount.objects.filter(transaction=transaction).first()
        buyer = locked_amount.user
        seller = User.objects.filter(email=locked_amount.seller_email).first()
        author = "BUYER" if user.is_buyer else "SELLER"
        priority = validated_data.get("priority")
        reason = validated_data.get("reason")
        description = validated_data.get("description")
        dispute = Dispute.objects.create(
            buyer=buyer,
            seller=seller,
            author=author,
            status="PENDING",
            transaction=transaction,
            priority=priority,
            description=description,
            reason=reason,
        )

        return dispute
