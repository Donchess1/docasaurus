from rest_framework import serializers

from console.models.transaction import EscrowMeta, Transaction


class EscrowTransactionMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscrowMeta
        fields = (
            "id",
            "author",
            "transaction_id",
            "buyer_id",
            "seller_id",
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
            "provider",
        )

    def validate_status(self, value):
        if value not in ["APPROVED", "REJECTED"]:
            raise serializers.ValidationError("Invalid status value")
        return value
