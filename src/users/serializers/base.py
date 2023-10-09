from rest_framework import serializers

from utils.email import CustomEmailField

from .models import User


class UserSerializer(serializers.ModelSerializer):
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
        )


class ForgotPasswordSerializer(serializers.Serializer):
    email = CustomEmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            return user
        else:
            raise serializers.ValidationError("Invalid email")


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate(self, attrs):
        password = attrs.get("password")
        return password
