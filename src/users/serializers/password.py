from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_address

User = get_user_model()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    platform = serializers.ChoiceField(
        choices=("BASE_PLATFORM", "MERCHANT_DASBOARD"), default="BASE_PLATFORM"
    )

    def validate(self, data):
        email = data.get("email")
        platform = data.get("platform")
        is_valid, message, validated_response = validate_email_address(
            email, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError({"email": message})

        user = User.objects.filter(
            email=validated_response["normalized_email"].lower()
        ).first()
        if not user:
            raise serializers.ValidationError(
                {"email": f"User with this email does not exist."}
            )

        if platform == "MERCHANT_DASBOARD" and not user.is_merchant:
            raise serializers.ValidationError(
                {"email": "Merchant account does not exist."}
            )

        data["email"] = validated_response["normalized_email"].lower()
        data["user"] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    hash = serializers.CharField()
    password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=True,
    )
    confirm_password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=True,
    )

    def validate_confirm_password(self, confirm_password):
        data = self.get_initial()
        password = data.get("password")
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        return confirm_password


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=True,
    )
    password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=True,
    )
    confirm_password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=True,
    )

    def validate(self, data):
        user = self.context["request"].user
        current_password = data.get("current_password")
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"password": "Current password is incorrect."}
            )

        if password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match"})

        if password == current_password:
            raise serializers.ValidationError(
                {"password": "New password cannot the current password"}
            )

        return data
