from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import UserProfile
from utils.email import validate_email_address
from utils.kyc import KYC_CHOICES
from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN, capitalize_fields_decorator

User = get_user_model()


@capitalize_fields_decorator(fields_to_capitalize=["name"])
class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    )
    metadata = serializers.SerializerMethodField()

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
            "metadata",
            "created_at",
            "updated_at",
        )

    def get_metadata(self, obj):
        user_profile_exists = UserProfile.objects.filter(user_id=obj).exists()
        meta_data = {}
        meta_data["default_user_type"] = (
            obj.userprofile.user_type if user_profile_exists else "UNDEFINED"
        )
        meta_data["flagged_status"] = (
            obj.userprofile.is_flagged if user_profile_exists else "UNDEFINED"
        )
        meta_data["deactivated_status"] = (
            obj.userprofile.is_deactivated if user_profile_exists else "UNDEFINED"
        )
        meta_data["avatar_url"] = (
            obj.userprofile.avatar if user_profile_exists else None
        )
        return meta_data


class UploadMediaSerializer(serializers.Serializer):
    image = serializers.FileField()
    destination = serializers.ChoiceField(
        choices=("BLOG", "DISPUTE_RESOLUTION", "AVATAR"),
        default="AVATAR",
        required=False,
    )


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
