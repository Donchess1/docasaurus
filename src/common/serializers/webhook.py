from rest_framework import serializers


class FlwWebhookSerializer(serializers.Serializer):
    event = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)


class StripeWebhookSerializer(serializers.Serializer):
    event = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)
