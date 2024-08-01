from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_address
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
            "is_merchant",
            "is_admin",
            "created_at",
            "updated_at",
        )


class UploadUserAvatarSerializer(serializers.Serializer):
    image = serializers.FileField()


class CheckUserByEmailViewSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return validated_response["normalized_email"].lower()


class CheckUserByPhoneNumberViewSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])


class UpdateKYCSerializer(serializers.Serializer):
    kyc_type = serializers.ChoiceField(choices=KYC_CHOICES)
    kyc_meta_id = serializers.UUIDField()


class OneTimeLoginCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with email does not exist.")
        return validated_response["normalized_email"].lower()
