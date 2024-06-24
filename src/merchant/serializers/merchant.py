from django.contrib.auth import get_user_model
from django.db import models, transaction
from rest_framework import serializers

from business.models.business import Business
from merchant.models import ApiKey, Customer, CustomerMerchant, Merchant, PayoutConfig
from merchant.utils import (
    create_or_update_customer_user,
    customer_phone_numer_exists_for_merchant,
    customer_with_email_exists_for_merchant,
    get_customer_merchant_instance,
)
from users.models import CustomUser, UserProfile
from users.models.bank_account import BankAccount
from users.serializers.profile import UserProfileSerializer
from utils.email import validate_email_body
from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN, generate_random_text

User = get_user_model()


class MerchantCreateSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN])

    class Meta:
        model = Merchant
        fields = (
            "name",
            "merchant_name",
            "description",
            "address",
            "phone",
            "email",
        )

    def validate(self, data):
        if User.objects.filter(phone=data["phone"]).exists():
            raise serializers.ValidationError(
                {"phone": "This phone number is already in use."}
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "This email address is already in use."}
            )

        data["email"] = data.get("email", "").lower()
        data["merchant_name"] = data.get("merchant_name", "").upper()

        return data

    @transaction.atomic
    def create(self, validated_data):
        password = generate_random_text(15)
        user_data = {
            "email": validated_data["email"],
            "phone": validated_data["phone"],
            "name": validated_data["name"],
            "password": password,
            "is_merchant": True,
            "is_verified": True,
        }
        user = User.objects.create_user(**user_data)

        profile_data = UserProfile.objects.create(
            user_id=user,
            user_type="MERCHANT",
            free_escrow_transactions=10,  # Confirm free-escrow transactions number from mgt
        )

        merchant_data = {
            "user_id": user,
            "name": validated_data.get("merchant_name"),
            "description": validated_data.get("description"),
            "address": validated_data.get("address"),
        }
        merchant = Merchant.objects.create(**merchant_data)
        config = PayoutConfig.objects.create(merchant=merchant, name="Default Config")
        return password, merchant


class MerchantSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = "__all__"

    def get_email(self, obj):
        return obj.user_id.email


class MerchantDetailSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = (
            "id",
            "name",
            "description",
            "address",
            "wallet_balance",
            "created_at",
            "updated_at",
        )

    def get_wallet_balance(self, obj):
        user_profile = UserProfile.objects.get(user_id=obj.user_id)
        # data = UserProfileSerializer(user_profile).data
        return str(user_profile.wallet_balance)


class CustomerUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    # merchant_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            # "id",
            "user_type",
            "created_at",
            "updated_at",
            "full_name",
            "phone_number",
            # "merchant_name",
            "email",
        )

    def get_merchant(self, *args, **kwargs):
        self.merchant = self.context.get("merchant", None)
        return self.merchant

    def get_merchant_customer_instance(self, obj, *args, **kwargs):
        merchant = self.get_merchant()
        return CustomerMerchant.objects.filter(customer=obj, merchant=merchant).first()

    def get_full_name(self, obj):
        customer_merchant_instance = self.get_merchant_customer_instance(obj)
        if customer_merchant_instance:
            return customer_merchant_instance.alternate_name
        return None

    def get_phone_number(self, obj):
        customer_merchant_instance = self.get_merchant_customer_instance(obj)
        if customer_merchant_instance:
            return customer_merchant_instance.alternate_phone_number
        return None

    def get_email(self, obj):
        return obj.user.email

    def get_user_type(self, obj):
        customer_merchant_instance = self.get_merchant_customer_instance(obj)
        if customer_merchant_instance:
            return customer_merchant_instance.user_type
        return None

    def get_merchant_name(self, obj):
        customer_merchant_instance = self.get_merchant_customer_instance(obj)
        if customer_merchant_instance:
            return customer_merchant_instance.merchant.name
        return None


class RegisterCustomerSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(
        choices=("BUYER", "SELLER", "CUSTOM"), required=False
    )
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN],
    )

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")
        merchant = self.context.get("merchant")

        obj = validate_email_body(email)
        if obj[0]:
            raise serializers.ValidationError({"email": obj[1]})

        if customer_phone_numer_exists_for_merchant(merchant, phone_number):
            raise serializers.ValidationError(
                {
                    "phone_number": "This phone number is already in use by another customer."
                }
            )

        user = User.objects.filter(email=email).first()
        if user:
            if customer_with_email_exists_for_merchant(merchant, user):
                raise serializers.ValidationError(
                    {"email": "This email is already in use by another customer."}
                )
        return data

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        customer_type = validated_data.get("customer_type")
        email = validated_data.get("email")
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        name = f"{first_name} {last_name}"
        phone_number = validated_data.get("phone_number")
        merchant = self.context.get("merchant")
        user, customer, error = create_or_update_customer_user(
            email, phone_number, name, customer_type, merchant
        )
        if error:
            raise serializers.ValidationError(error)
        return user


class CustomerWidgetSessionSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()

    def validate(self, data):
        email = data.get("customer_email")
        merchant = self.context.get("merchant")

        customer_instance = get_customer_merchant_instance(email, merchant)
        if not customer_instance:
            raise serializers.ValidationError({"user": "Customer does not exist."})
        data["customer_instance"] = customer_instance
        return data


class CustomerWidgetSessionPayloadSerializer(serializers.Serializer):
    widget_url = serializers.URLField()
    session_lifetime = serializers.CharField()


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ["name"]


class PayoutConfigSerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = PayoutConfig
        fields = [
            "id",
            "merchant",
            "buyer_charge_type",
            "buyer_amount",
            "name",
            "seller_charge_type",
            "seller_amount",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_buyer_amount(self, value):
        buyer_charge_type = self.initial_data.get("buyer_charge_type")
        if (
            buyer_charge_type == "PERCENTAGE" and value > 100
        ) or buyer_charge_type == "NO_FEES":
            return 0
        return value

    def validate_seller_amount(self, value):
        seller_charge_type = self.initial_data.get("seller_charge_type")
        if (
            seller_charge_type == "PERCENTAGE" and value > 100
        ) or seller_charge_type == "NO_FEES":
            return 0
        return value

    def validate(self, data):
        name = data.get("name")
        merchant = self.context.get("merchant")
        if PayoutConfig.objects.filter(merchant=merchant, name=name).exists():
            raise serializers.ValidationError(
                {"name": "Payout config with this name already exists."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        PayoutConfig.objects.filter(merchant=validated_data["merchant"]).update(
            is_active=False
        )
        return super().create(validated_data)
