import json

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from business.models.business import Business
from merchant.models import Merchant, PayoutConfig
from users.models.bank_account import BankAccount
from users.models.kyc import UserKYC
from users.models.profile import UserProfile
from users.models.wallet import Wallet
from utils.email import validate_email_address
from utils.utils import (
    PHONE_NUMBER_SERIALIZER_REGEX_NGN,
    REGISTRATION_REFERRER,
    SYSTEM_CURRENCIES,
)

User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])
    email = serializers.EmailField()
    referrer = serializers.ChoiceField(choices=REGISTRATION_REFERRER, default="OTHERS")

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "referrer",
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

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return validated_response["normalized_email"].lower()

    def validate_phone(self, phone):
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return phone

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        name = f"{first_name} {last_name}"
        user_data = {
            "email": validated_data["email"],
            "password": validated_data["password"],
            "phone": validated_data["phone"],
            "name": name,
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
        for currency in SYSTEM_CURRENCIES:  # Consider creating wallets after KYC
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
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    business_name = serializers.CharField()
    business_description = serializers.CharField()
    address = serializers.CharField()
    bank_name = serializers.CharField()
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    bank_code = serializers.CharField()
    referrer = serializers.ChoiceField(choices=REGISTRATION_REFERRER, default="OTHERS")

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
            "is_buyer",
            "referrer",
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

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return validated_response["normalized_email"].lower()

    def validate_phone(self, phone):
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return phone

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        name = f"{first_name} {last_name}"
        user_data = {
            "email": validated_data["email"],
            "password": validated_data["password"],
            "phone": validated_data["phone"],
            "name": name,
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
        for currency in SYSTEM_CURRENCIES:
            Wallet.objects.create(
                user=user,
                currency=currency,
            )
        return user


class RegisterMerchantSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    merchant_name = serializers.CharField()
    description = serializers.CharField()
    address = serializers.CharField()
    buyer_charge_type = serializers.ChoiceField(
        choices=PayoutConfig.PAYMENT_TYPE_CHOICES
    )
    seller_charge_type = serializers.ChoiceField(
        choices=PayoutConfig.PAYMENT_TYPE_CHOICES
    )
    buyer_amount = serializers.IntegerField()
    seller_amount = serializers.IntegerField()

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
            "merchant_name",
            "description",
            "address",
            "buyer_charge_type",
            "seller_charge_type",
            "buyer_amount",
            "seller_amount",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_email(self, value):
        is_valid, message, validated_response = validate_email_address(
            value, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError(message)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return validated_response["normalized_email"].lower()

    def validate_phone(self, phone):
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return phone

    def validate_buyer_amount(self, value):
        buyer_charge_type = self.initial_data.get("buyer_charge_type")
        if buyer_charge_type == "NO_FEES":
            value = 0
        if buyer_charge_type == "PERCENTAGE" and value > 100:
            raise serializers.ValidationError("Percentage should not exceed 100.")
        return value

    def validate_seller_amount(self, value):
        seller_charge_type = self.initial_data.get("seller_charge_type")
        if seller_charge_type == "NO_FEES":
            value = 0
        if seller_charge_type == "PERCENTAGE" and value > 100:
            raise serializers.ValidationError("Percentage should not exceed 100.")
        return value

    def validate(self, data):
        name = data.get("name")
        merchant = self.context.get("merchant")
        if PayoutConfig.objects.filter(merchant=merchant, name=name).exists():
            raise serializers.ValidationError(
                {"name": "Payout configuration with this name already exists."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        merchant_name = validated_data.get("merchant_name")
        email = validated_data["email"]
        name = f"{first_name} {last_name}"
        password = validated_data["password"]
        phone = validated_data["phone"]

        user_data = {
            "email": email,
            "password": password,
            "phone": phone,
            "name": name,
            "is_merchant": True,
        }
        user = User.objects.create_user(**user_data)
        user.set_password(validated_data["password"])
        user.save()
        user.create_wallet()

        profile_data = UserProfile.objects.create(
            user_id=user,
            user_type="MERCHANT",
            free_escrow_transactions=10,
        )
        merchant_data = {
            "user_id": user,
            "name": merchant_name.upper(),
            "description": validated_data.get("description"),
            "address": validated_data.get("address"),
        }
        merchant = Merchant.objects.create(**merchant_data)

        buyer_charge_type = validated_data.get("buyer_charge_type")
        seller_charge_type = validated_data.get("seller_charge_type")
        buyer_amount = validated_data.get("buyer_amount")
        seller_amount = validated_data.get("seller_amount")
        payout_config_data = {
            "name": "Default Config",
            "merchant": merchant,
            "buyer_charge_type": buyer_charge_type,
            "buyer_amount": buyer_amount,
            "seller_charge_type": seller_charge_type,
            "seller_amount": seller_amount,
        }
        PayoutConfig.objects.create(
            **payout_config_data,
        )
        return user
