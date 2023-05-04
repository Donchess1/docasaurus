from rest_framework import serializers


class ValidatedNINPayloadSerializer(serializers.Serializer):
    nin = serializers.CharField(max_length=11, min_length=11)
    first_name = serializers.CharField()
    middle_name = serializers.CharField()
    last_name = serializers.CharField()
    telephoneno = serializers.CharField()
    profession = serializers.CharField()
    title = serializers.CharField()
    birthdate = serializers.CharField()
    birthstate = serializers.CharField()
    birthcountry = serializers.CharField()
