from rest_framework import serializers

from console.models.identity import NINIdentity


class NINIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NINIdentity
        fields = (
            "id",
            "number",
            "meta",
            "created_at",
            "updated_at",
        )
