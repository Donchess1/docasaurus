from rest_framework import serializers

from console.serializers.overview import BaseSummarySerializer, StatusCountSerializer


class DisputePrioritySerializer(serializers.Serializer):
    PENDING = StatusCountSerializer()
    PROGRESS = StatusCountSerializer()
    RESOLVED = StatusCountSerializer()
    TOTAL = StatusCountSerializer()


class DisputeSummarySerializer(BaseSummarySerializer):
    low = DisputePrioritySerializer()
    medium = DisputePrioritySerializer()
    high = DisputePrioritySerializer()
