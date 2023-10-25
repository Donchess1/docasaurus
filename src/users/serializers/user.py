from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_body
from utils.kyc import KYC_CHOICES
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


class CheckUserByEmailViewSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        obj = validate_email_body(value)
        if obj[0]:
            raise serializers.ValidationError(obj[1])
        return value


class UpdateKYCSerializer(serializers.Serializer):
    kyc_type = serializers.ChoiceField(choices=KYC_CHOICES)
    kyc_meta_id = serializers.UUIDField()
