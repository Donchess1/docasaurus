from django.contrib.auth import get_user_model
from rest_framework import serializers

from utils.email import validate_email_body

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
        obj = validate_email_body(value)
        if obj[0]:
            raise serializers.ValidationError(obj[1])
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value
