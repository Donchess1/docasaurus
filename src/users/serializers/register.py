import json

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from business.models.business import Business
from users.models.bank_account import BankAccount
from users.models.kyc import UserKYC
from users.models.profile import UserProfile
from users.models.wallet import Wallet
from utils.utils import (
    CURRENCIES,
    PHONE_NUMBER_SERIALIZER_REGEX_NGN,
    REGISTRATION_REFERRER,
)

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])
    referrer = serializers.ChoiceField(choices=REGISTRATION_REFERRER)

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

    def validate_phone(self, phone):
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return phone

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        user_data = {
            "email": validated_data["email"],
            "password": validated_data["password"],
            "phone": validated_data["phone"],
            "name": validated_data["name"],
            "is_buyer": True,
        }
        user = User.objects.create_user(**user_data)
        user.set_password(validated_data["password"])
        user.save()
        # bank_account = BankAccount.objects.create(user_id=user)
        profile = UserProfile.objects.create(
            user_id=user,
            # bank_account_id=bank_account,
            user_type="BUYER",
            free_escrow_transactions=5,
            referrer=validated_data.get("referrer"),
        )
        for currency in CURRENCIES:  # Consider creating wallets after KYC
            Wallet.objects.create(
                user=user,
                currency=currency,
            )
        return user


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
    referrer = serializers.ChoiceField(choices=REGISTRATION_REFERRER)

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

    def validate_phone(self, phone):
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return phone

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        user_data = {
            "email": validated_data["email"],
            "password": validated_data["password"],
            "phone": validated_data["phone"],
            "name": validated_data["name"],
            "is_seller": True,
        }
        user = User.objects.create_user(**user_data)
        user.set_password(validated_data["password"])
        user.save()
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
            free_escrow_transactions=10,
            referrer=validated_data.get("referrer"),
        )
        for currency in CURRENCIES:
            Wallet.objects.create(
                user=user,
                currency=currency,
            )
        return user
