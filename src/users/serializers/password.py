from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_address

User = get_user_model()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        user = User.objects.filter(
            email=validated_response["normalized_email"].lower()
        ).first()
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")
        return validated_response["normalized_email"].lower()


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
