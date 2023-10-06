from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    )

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "is_verified",
            "is_buyer",
            "is_seller",
            "created_at",
            "updated_at",
        )


class UploadUserAvatarSerializer(serializers.Serializer):
    image = serializers.FileField()
