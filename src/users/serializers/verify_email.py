from rest_framework import serializers


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    temp_id = serializers.CharField()


class VerifiedOTPPayloadSerializer(serializers.Serializer):
    email = serializers.EmailField()
