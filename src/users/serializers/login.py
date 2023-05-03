from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .user import UserSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )


class LoginPayloadSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserSerializer()
