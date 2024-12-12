from django.contrib.auth import get_user_model
from rest_framework import serializers

from console.models.dispute import Dispute
from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from merchant.utils import transactions_delivery_date_has_not_elapsed

User = get_user_model()


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
        if transactions_delivery_date_has_not_elapsed([str(value.id)]):
            raise serializers.ValidationError("Delivery date is not due yet")
        if Dispute.objects.filter(transaction=value).exists():
            raise serializers.ValidationError(
                "Dispute already exists for this transaction."
            )
        if value.status == "FUFILLED":
            raise serializers.ValidationError("Transaction was already fulfilled!")
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(instance, Dispute):
            transaction = instance.transaction
            representation["transaction_ref"] = transaction.reference
            if instance.author == "BUYER":
                representation["raised_by"] = {
                    "user_id": instance.buyer.id,
                    "name": instance.buyer.name,
                    "email": instance.buyer.email,
                    "role": "BUYER",
                }
                representation["raised_against"] = {
                    "user_id": instance.seller.id,
                    "name": instance.seller.name,
                    "email": instance.seller.email,
                    "role": "SELLER",
                }
            elif instance.author == "SELLER":
                representation["raised_by"] = {
                    "user_id": instance.seller.id,
                    "name": instance.seller.name,
                    "email": instance.seller.email,
                    "role": "SELLER",
                }
                representation["raised_against"] = {
                    "user_id": instance.buyer.id,
                    "name": instance.buyer.name,
                    "email": instance.buyer.email,
                    "role": "BUYER",
                }
        return representation


class ResolveDisputeSerializer(serializers.Serializer):
    destination = serializers.ChoiceField(choices=("BUYER", "SELLER"))
    supporting_document = serializers.URLField(required=False)
    supporting_note = serializers.CharField(required=False)
