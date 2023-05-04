from rest_framework import serializers


class ValidateNINBVNSerializer(serializers.Serializer):
    number = serializers.CharField(max_length=11, min_length=11)


class ValidatedBVNPayloadSerializer(serializers.Serializer):
    bvn = serializers.CharField(max_length=11, min_length=11)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_of_birth = serializers.CharField()
