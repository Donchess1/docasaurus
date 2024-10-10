from rest_framework import serializers

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from transaction.serializers.locked_amount import LockedAmountSerializer
from transaction.services import get_escrow_transaction_parties_info


class EscrowTransactionMetaSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    parties = serializers.SerializerMethodField()

    class Meta:
        model = EscrowMeta
        fields = (
            "id",
            "author",
            "author_name",
            "partner_email",
            "purpose",
            "item_type",
            "item_quantity",
            "delivery_date",
            "parties",
            "delivery_tolerance",
            "buyer_consent_to_unlock",
            "charge",
            "meta",
            "created_at",
            "updated_at",
        )

    def get_author_name(self, obj):
        return obj.transaction_id.user_id.name

    def get_parties(self, obj):
        parties = get_escrow_transaction_parties_info(obj.transaction_id)
        return parties


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
            "merchant",
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
            "merchant",
            "amount",
            "charge",
            "remitted_amount",
            "currency",
            "locked_amount",
            "escrow_metadata",
            "provider",
        )

    def __init__(self, *args, **kwargs):
        super(UserTransactionSerializer, self).__init__(*args, **kwargs)
        if self.context.get("hide_escrow_details"):
            self.fields.pop("escrow_metadata")
        if self.context.get("hide_locked_amount"):
            self.fields.pop("locked_amount")

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
            raise serializers.ValidationError(
                "Invalid status value. Must be 'APPROVED' or 'REJECTED'"
            )
        return value


class UpdateEscrowTransactionSerializer(serializers.Serializer):
    REJECTED_REASONS_CHOICES = (
        ("WRONG_AMOUNT", "WRONG_AMOUNT"),
        ("WRONG_DESCRIPTION", "WRONG_DESCRIPTION"),
        ("WRONG_ITEM_CHOICE", "WRONG_ITEM_CHOICE"),
        ("WRONG_QUANTITY", "WRONG_QUANTITY"),
        ("WRONG_DELIVERY_DATE", "WRONG_DELIVERY_DATE"),
    )

    status = serializers.ChoiceField(choices=("APPROVED", "REJECTED"))
    rejected_reason = serializers.MultipleChoiceField(
        choices=REJECTED_REASONS_CHOICES, allow_null=True, required=False
    )

    def validate(self, data):
        status = data.get("status")
        rejected_reason = data.get("rejected_reason")

        if status == "REJECTED" and not rejected_reason:
            raise serializers.ValidationError(
                {
                    "rejected_reason": "Rejected reason is required when status is 'REJECTED'."
                }
            )

        return data


class RevokeEscrowTransactionSerializer(serializers.Serializer):
    reason = serializers.CharField()
    supporting_document = serializers.URLField(required=False)
