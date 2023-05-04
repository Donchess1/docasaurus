from rest_framework import serializers


class ValidatePassportSerializer(serializers.Serializer):
    number = serializers.CharField()
    last_name = serializers.CharField()


class ValidatedPassportPayloadSerializer(serializers.Serializer):
    number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    middle_name = serializers.CharField()
    dob = serializers.CharField()
    mobile = serializers.CharField()
    gender = serializers.CharField()
