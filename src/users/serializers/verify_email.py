from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_address

User = get_user_model()


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    temp_id = serializers.CharField()


class VerifiedOTPPayloadSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    old_temp_id = serializers.CharField(required=False)

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(value, check_deliverability=True)
        if is_valid:
            raise serializers.ValidationError(message)
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return validated_response["normalized_email"].lower()
