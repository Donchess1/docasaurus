from rest_framework import serializers


class StatesListSerializer(serializers.Serializer):
    state = serializers.CharField()
    alias = serializers.CharField()
    capital = serializers.CharField()


class StateLGAListSerializer(serializers.Serializer):
    lgas = serializers.ListField(child=serializers.CharField())
