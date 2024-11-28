from django.contrib.auth import get_user_model
from django.db import models, transaction
from rest_framework import serializers

from business.models.business import Business
from console.serializers.overview import UserSystemMetricsSerializer
from console.utils import get_user_system_metrics
from merchant.models import ApiKey, Customer, CustomerMerchant, Merchant, PayoutConfig
from merchant.utils import (
    create_or_update_customer_user,
    customer_phone_numer_exists_for_merchant,
    customer_with_email_exists_for_merchant,
    get_customer_merchant_instance,
)
from users.models import CustomUser, UserProfile
from users.models.bank_account import BankAccount
from users.models.wallet import Wallet
from users.serializers.profile import UserProfileSerializer
from users.serializers.wallet import UserWalletSerializer
from utils.email import validate_email_address
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
        user.create_wallet()

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
    owner = serializers.SerializerMethodField()
    wallets = serializers.SerializerMethodField()
    system_metrics = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = (
            "id",
            "name",
            "owner",
            "user_id",
            "email",
            "wallets",
            "system_metrics",
            "is_active",
            "description",
            "address",
            "created_at",
            "updated_at",
        )

    def __init__(self, *args, **kwargs):
        super(MerchantSerializer, self).__init__(*args, **kwargs)
        if self.context.get("hide_wallet_details"):
            self.fields.pop("wallets")
        if not self.context.get("show_system_metrics"):
            self.fields.pop("system_metrics")

    def get_email(self, obj):
        return obj.user_id.email

    def get_owner(self, obj):
        return obj.user_id.name

    def get_user_id(self, obj):
        return obj.user_id.id

    def get_wallets(self, obj):
        show_complete_wallet_info = self.context.get("show_complete_wallet_info")
        _, wallets = obj.user_id.get_wallets()
        serializer = (
            UserWalletSerializer
            if show_complete_wallet_info
            else MerchantWalletSerializer
        )
        return serializer(wallets, many=True).data

    def get_system_metrics(self, obj):
        user = obj.user_id
        metrics_data = get_user_system_metrics(user)
        serializer = UserSystemMetricsSerializer(metrics_data)
        return serializer.data

    def get_is_active(self, obj):
        # Check if UserProfile exists and then access is_deactivated
        user_profile = getattr(obj.user_id, "userprofile", None)
        if user_profile:
            return not user_profile.is_deactivated
        return True


class MerchantWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = (
            "balance",
            "currency",
        )


class MerchantCustomerWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = (
            # "id",
            "currency",
            "balance",
            "locked_amount_outward",
            "locked_amount_inward",
            "unlocked_amount",
            "withdrawn_amount",
            # "created_at",
            # "updated_at",
        )


class CustomerUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    wallets = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "user_type",
            "user_id",
            "created_at",
            "updated_at",
            "full_name",
            "phone_number",
            "email",
            "wallets",
        )

    def __init__(self, *args, **kwargs):
        super(CustomerUserProfileSerializer, self).__init__(*args, **kwargs)
        if self.context.get("hide_wallet_details"):
            self.fields.pop("wallets")
        if self.context.get("hide_user_id"):
            self.fields.pop("user_id")

    def get_customermerchant(self, obj):
        merchant = self.context.get("merchant")
        if merchant:
            try:
                return obj.customermerchant_set.get(merchant=merchant)
            except CustomerMerchant.DoesNotExist:
                return None
        return None

    def get_full_name(self, obj):
        customermerchant = self.get_customermerchant(obj)
        if customermerchant:
            return customermerchant.alternate_name
        return obj.user.name

    def get_phone_number(self, obj):
        customermerchant = self.get_customermerchant(obj)
        if customermerchant:
            return customermerchant.alternate_phone_number
        return obj.user.phone

    def get_email(self, obj):
        return obj.user.email

    def get_user_type(self, obj):
        customermerchant = self.get_customermerchant(obj)
        if customermerchant:
            return customermerchant.user_type
        return None

    def get_user_id(self, obj):
        return obj.user.id

    def get_wallets(self, obj):
        customermerchant = self.get_customermerchant(obj)
        if customermerchant:
            wallets = Wallet.objects.filter(user=customermerchant.customer.user)
            return MerchantCustomerWalletSerializer(wallets, many=True).data
        return []


class RegisterCustomerSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(
        choices=("BUYER", "SELLER", "CUSTOM"), required=False
    )
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    )

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number", None)
        merchant = self.context.get("merchant")

        is_valid, message, validated_response = validate_email_address(
            email, check_deliverability=True
        )
        if not is_valid:
            raise serializers.ValidationError({"email": message})

        if phone_number and customer_phone_numer_exists_for_merchant(
            merchant, phone_number
        ):
            raise serializers.ValidationError(
                {"phone_number": "Customer with phone number already exists."}
            )

        user = User.objects.filter(
            email=validated_response["normalized_email"].lower()
        ).first()
        if user:
            if customer_with_email_exists_for_merchant(merchant, user):
                raise serializers.ValidationError(
                    {"email": "Customer with email already exists."}
                )
        data["email"] = validated_response["normalized_email"].lower()
        return data

    @transaction.atomic
    def create(self, validated_data):
        customer_type = validated_data.get("customer_type", "CUSTOM")
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


class UpdateCustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    )

    def validate(self, data):
        if not data:
            raise serializers.ValidationError(
                {"error": "At least one field must be updated."}
            )
        phone_number = data.get("phone_number")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        merchant = self.context.get("merchant")

        if customer_phone_numer_exists_for_merchant(merchant, phone_number):
            raise serializers.ValidationError(
                {"phone_number": "Customer with phone number already exists."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        customer_merchant_instance = self.context.get("customer_merchant_instance")
        customer_merchant_instance_name = customer_merchant_instance.alternate_name
        first_name = validated_data.get(
            "first_name", customer_merchant_instance_name.split(" ")[0]
        )
        last_name = validated_data.get(
            "last_name", customer_merchant_instance_name.split(" ")[1]
        )
        name = f"{first_name} {last_name}"
        phone_number = validated_data.get(
            "phone_number", customer_merchant_instance.alternate_phone_number
        )
        merchant = self.context.get("merchant")
        customer_merchant_instance.alternate_phone_number = phone_number
        customer_merchant_instance.alternate_name = name
        customer_merchant_instance.name_match = (
            True if name == customer_merchant_instance.customer.user.name else False
        )
        phone_number_match = (
            True
            if phone_number == customer_merchant_instance.customer.user.phone
            else False
        )
        customer_merchant_instance.save()
        return customer_merchant_instance


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

    def __init__(self, *args, **kwargs):
        super(PayoutConfigSerializer, self).__init__(*args, **kwargs)
        if self.context.get("view_action") in ["list", "retrieve"]:
            self.fields.pop("merchant")

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
                {"name": "Payout configuration with this name already exists."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        PayoutConfig.objects.filter(merchant=validated_data["merchant"]).update(
            is_active=False
        )
        return super().create(validated_data)
