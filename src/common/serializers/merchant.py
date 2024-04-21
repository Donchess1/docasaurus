from rest_framework import serializers


class TrimMerchantTokenSerializer(serializers.Serializer):
    key = serializers.CharField()


class TrimMerchantTokenPayloadSerializer(serializers.Serializer):
    token = serializers.CharField()
    merchant_id = serializers.UUIDField()
