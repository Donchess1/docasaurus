from rest_framework import serializers


class FlwWebhookSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.JSONField()


class FlwPayoutSerializer(serializers.Serializer):
    data = serializers.JSONField()


class FlwTransferCallbackSerializer(serializers.Serializer):
    transfer = serializers.JSONField(required=False)
    data = serializers.JSONField(required=False)

    def validate(self, attrs):
        transfer_data = attrs.get("transfer")
        data_data = attrs.get("data")

        if not transfer_data and not data_data:
            raise serializers.ValidationError(
                "At least one of 'transfer' or 'data' must be provided."
            )

        return attrs
