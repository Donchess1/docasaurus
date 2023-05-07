from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


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
