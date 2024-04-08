from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from business.models.business import Business
from merchant.models import Customer, Merchant
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
            "enable_payout_splitting",
            "payout_splitting_ratio",
            "phone",
            "email",
        )

    def validate(self, data):
        enable_payout_splitting = data.get("enable_payout_splitting", False)
        payout_splitting_ratio = data.get("payout_splitting_ratio", None)

        if User.objects.filter(phone=data["phone"]).exists():
            raise serializers.ValidationError(
                {"phone": "This phone number is already in use."}
            )

        if enable_payout_splitting and payout_splitting_ratio is None:
            raise serializers.ValidationError(
                {
                    "payout_splitting_ratio": "Payout splitting ratio must be provided when enabled."
                }
            )

        data["email"] = data.get("email", "").lower()
        data["merchant_name"] = data.get("merchant_name", "").upper()

        return data

    @transaction.atomic
    def create(self, validated_data):
        user_data = {
            "email": validated_data["email"],
            "phone": validated_data["phone"],
            "name": validated_data["name"],
            "password": generate_random_text(15),
            "is_merchant": True,
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
            "enable_payout_splitting": validated_data.get("enable_payout_splitting"),
            "payout_splitting_ratio": validated_data.get("payout_splitting_ratio"),
        }
        merchant = Merchant.objects.create(**merchant_data)
        return merchant


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = "__all__"


class MerchantDetailSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = "__all__"

    def get_user_profile(self, obj):
        user_profile = UserProfile.objects.get(user_id=obj.user_id)
        return UserProfileSerializer(user_profile).data


class CustomerUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "user_type",
            "created_at",
            "updated_at",
            "full_name",
            "phone_number",
            "email",
        )
    
    def get_full_name(self, obj):
        return obj.user.name
    
    def get_phone_number(self, obj):
        return obj.user.phone
    
    def get_email(self, obj):
        return obj.user.email
    
    def get_user_type(self, obj):
        return obj.user.userprofile.user_type

class RegisterCustomerSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(choices=("BUYER", "SELLER"))
    email = serializers.EmailField()
    name = serializers.CharField(required=False)
    phone_number = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN],
    )

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")

        obj = validate_email_body(email)
        if obj[0]:
            raise serializers.ValidationError({"email": obj[1]})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "This email is already in use."}
            )

        if phone_number and User.objects.filter(phone=phone_number).exists():
            raise serializers.ValidationError(
                {"phone_number": "This phone number is already in use."}
            )

        return data

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        customer_type = validated_data.get("customer_type")
        merchant = self.context.get("merchant")

        user_data = {
            "email": validated_data["email"],
            "phone": validated_data["phone_number"],
            "name": validated_data["name"],
            "password": generate_random_text(15),
            f"is_{customer_type.lower()}": True,
        }
        user = User.objects.create_user(**user_data)

        profile_data = UserProfile.objects.create(
            user_id=user,
            user_type=customer_type,
            free_escrow_transactions=10 if customer_type == "SELLER" else 5,
        )

        customer = Customer.objects.create(user=user)
        customer.merchants.add(merchant)

        return user
