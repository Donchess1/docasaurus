from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from utils.email import validate_email_address

from .user import UserSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return validated_response["normalized_email"].lower()


class LoginPayloadSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserSerializer()
