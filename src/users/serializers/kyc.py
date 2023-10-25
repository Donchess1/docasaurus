from rest_framework import serializers

from users.models.kyc import UserKYC


class UserKYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserKYC
        fields = "__all__"
