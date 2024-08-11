from rest_framework import serializers


class BaseSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    total = serializers.IntegerField()


class StatusCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class VolumeCountSerializer(serializers.Serializer):
    volume = serializers.FloatField()
    count = serializers.IntegerField()
