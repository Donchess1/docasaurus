from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from utils.email import validate_email_body

from .user import UserSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate_email(self, value):
        obj = validate_email_body(value)
        if obj[0]:
            raise serializers.ValidationError(obj[1])
        return value


class LoginPayloadSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserSerializer()
