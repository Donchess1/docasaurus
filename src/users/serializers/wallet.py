from rest_framework import serializers

from users.models.wallet import Wallet


class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = (
            "id",
            "currency",
            "balance",
            "locked_amount_outward",
            "locked_amount_inward",
            "unlocked_amount",
            "withdrawn_amount",
            "created_at",
            "updated_at",
        )
