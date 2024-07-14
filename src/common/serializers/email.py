from rest_framework import serializers


class ValidateEmailAddressSerializer(serializers.Serializer):
    email = serializers.EmailField()
