from rest_framework import serializers

from console.models.transaction import LockedAmount


class LockedAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LockedAmount
        fields = (
            "id",
            "seller_email",
            "amount",
            "status",
        )
