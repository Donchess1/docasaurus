from rest_framework import serializers


class FlwWebhookSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.JSONField()
class FlwTransferCallbackSerializer(serializers.Serializer):
    event = serializers.CharField()
    transfer = serializers.JSONField()
