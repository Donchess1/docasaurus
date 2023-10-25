import json

from django.contrib.auth import get_user_model
from rest_framework import serializers

from business.models.business import Business
from users.models.bank_account import BankAccount
from users.models.kyc import UserKYC
from users.models.profile import UserProfile
from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "password",
            "is_buyer",
            "is_seller",
            "is_verified",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_buyer": {"read_only": True},
            "is_seller": {"read_only": True},
            "is_verified": {"read_only": True},
        }


class RegisteredUserPayloadSerializer(serializers.Serializer):
    temp_id = serializers.CharField()
    email = serializers.EmailField()


class RegisterSellerSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])
    business_name = serializers.CharField()
    business_description = serializers.CharField()
    address = serializers.CharField()
    bank_name = serializers.CharField()
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    bank_code = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "password",
            "is_buyer",
            "is_seller",
            "is_verified",
            "business_name",
            "business_description",
            "address",
            "bank_name",
            "bank_code",
            "account_number",
            "account_name",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_buyer": {"read_only": True},
            "is_seller": {"read_only": True},
            "is_verified": {"read_only": True},
        }

    def create(self, validated_data):
        # Create user
        user_data = {
            "email": validated_data["email"],
            "password": validated_data["password"],
            "phone": validated_data["phone"],
            "name": validated_data["name"],
            "is_seller": True,
        }
        user = User.objects.create_user(**user_data)

        # Create bank account
        bank_account_data = {
            "user_id": user,
            "bank_name": validated_data.get("bank_name"),
            "bank_code": validated_data.get("bank_code"),
            "account_name": validated_data.get("account_name"),
            "account_number": validated_data.get("account_number"),
        }
        bank_account = BankAccount.objects.create(**bank_account_data)

        # Create business
        business_data = {
            "user_id": user,
            "name": validated_data.get("business_name"),
            "description": validated_data.get("business_description"),
            "address": validated_data.get("address"),
        }
        business = Business.objects.create(**business_data)
        # Create User profile
        profile_data = UserProfile.objects.create(
            user_id=user,
            business_id=business,
            bank_account_id=bank_account,
            user_type="SELLER",
        )
        return user
