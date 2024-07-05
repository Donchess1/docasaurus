from rest_framework import serializers


class FlwWebhookSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.JSONField()
