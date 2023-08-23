from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from transaction.serializers.locked_amount import LockedAmountSerializer


class EscrowTransactionMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscrowMeta
        fields = (
            "id",
            "author",
            "partner_email",
            "purpose",
            "item_type",
            "item_quantity",
            "delivery_date",
            "delivery_tolerance",
            "charge",
            "meta",
            "created_at",
            "updated_at",
        )


class UserTransactionSerializer(serializers.ModelSerializer):
    locked_amount = serializers.SerializerMethodField()
    escrow_metadata = serializers.SerializerMethodField()

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
            "verified",
            "locked_amount",
            "escrow_metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "provider_tx_reference",
            "meta",
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
            "escrow_metadata",
            "provider",
        )

    def get_locked_amount(self, obj):
        instance = LockedAmount.objects.filter(transaction=obj).first()
        if not instance:
            return None
        serializer = LockedAmountSerializer(instance=instance)
        return serializer.data

    def get_escrow_metadata(self, obj):
        instance = EscrowMeta.objects.filter(transaction_id=obj).first()
        if not instance:
            return None
        serializer = EscrowTransactionMetaSerializer(instance=instance)
        return serializer.data

    def validate_status(self, value):
        if value not in ["APPROVED", "REJECTED"]:
            raise serializers.ValidationError("Invalid status value")
        return value
