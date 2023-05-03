from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "password",
            "is_buyer",
            "is_seller",
            "is_verified",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_buyer": {"read_only": True},
            "is_seller": {"read_only": True},
            "is_verified": {"read_only": True},
        }


class RegisteredUserPayloadSerializer(serializers.Serializer):
    temp_id = serializers.CharField()
