from rest_framework import serializers


class FlwBankTransferSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.JSONField()
