from django.contrib.auth import get_user_model
from django.db import models, transaction
from rest_framework import serializers

from business.models.business import Business
from merchant.models import Customer, CustomerMerchant, Merchant
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


def create_or_update_customer(email, phone_number, customer_type, merchant):
    """
    Creates or updates a customer with the given email, phone number & customer type.
    If a user with the given email exists, fetch the user and see if there is a CustomerMerchant instance linked to the merchant and the customer linked to this user (if existing)
     linked to the merchant.
    If the user with the given email and phone number does not exist,
    it will be created.
    If the user with both email and phone number exists but not linked to merchant,
    it will be linked to the merchant.
    If the user with the same email exists but different phone number,
    it will be updated.
    """
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        existing_customer = (
            Customer.objects.filter(user=existing_user)
            .filter(merchants=merchant)
            .first()
        )  # This means there is a customer with this email address already linked to merchant
        if existing_customer:
            return existing_user, existing_customer, None

        customer, created = Customer.objects.get_or_create(user=existing_user)
        customer.merchants.add(merchant)
        if existing_user.phone != phone_number:
            CustomerMerchant.objects.get_or_create(
                customer=customer,
                merchant=merchant,
                alternate_phone_number=phone_number,
                user_type=customer_type,
            )
            customer.alternate_phone_number = phone_number
            customer.save()
        return existing_user, customer, None

    existing_user = User.objects.filter(email=email).first()
    existing_customer = None

    if existing_user:
        existing_customer = (
            Customer.objects.filter(user=existing_user)
            .filter(merchants=merchant)
            .first()
        )

    if existing_user and existing_customer:
        return existing_user, existing_customer, None

    # If user with both email and phone number exists but not linked to merchant
    if existing_user and not existing_customer:
        # Create a new Customer instance linked to the merchant
        customer = Customer.objects.create(user=existing_user)
        customer.merchants.add(merchant)
        return existing_user, customer, None

    # If user with the same email exists but different phone number
    if existing_user and existing_user.phone != phone_number:
        # Update the alternate phone number in the CustomerMerchant model
        existing_customer_merchant = CustomerMerchant.objects.filter(
            customer__user=existing_user
        ).first()
        if existing_customer_merchant:
            existing_customer_merchant.alternate_phone_number = phone_number
            existing_customer_merchant.save()
        else:
            CustomerMerchant.objects.create(
                customer=existing_user.customer,
                merchant=merchant,
                alternate_phone_number=phone_number,
            )
        return existing_user, existing_user.customer, None

    user_data = {
        "email": email,
        "phone": phone_number,
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
    CustomerMerchant.objects.create(
        customer=customer,
        merchant=merchant,
        alternate_phone_number=phone_number,
        user_type=customer_type,
    )
    return user, customer, None


class RegisterCustomerSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(choices=("BUYER", "SELLER"))
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN],
    )

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")

        obj = validate_email_body(email)
        if obj[0]:
            raise serializers.ValidationError({"email": obj[1]})

        merchant = self.context.get("merchant")

        # Check if a customer with the user linked to email or phone exists for the merchant
        existing_customer = (
            Customer.objects.filter(
                models.Q(user__email=email) | models.Q(user__phone=phone_number)
            )
            .filter(merchants=merchant)
            .first()
        )

        # Check if a customer with the provided phone number exists as an alternate phone number
        if not existing_customer:
            existing_customer_merchant = CustomerMerchant.objects.filter(
                alternate_phone_number=phone_number, merchant=merchant
            ).first()
            if existing_customer_merchant:
                existing_customer = existing_customer_merchant.customer

        if existing_customer:
            error_data = {}
            if existing_customer.user.email == email:
                error_data[
                    "email"
                ] = "Customer with this email already exists for this merchant."
            if existing_customer.user.phone == phone_number:
                error_data[
                    "phone_number"
                ] = "Customer with this phone number already exists for this merchant."

            raise serializers.ValidationError(error_data)

        return data

    def to_internal_value(self, data):
        data["email"] = data.get("email", "").lower()
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        customer_type = validated_data.get("customer_type")
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")
        merchant = self.context.get("merchant")
        user, customer, error = create_or_update_customer(
            email, phone_number, customer_type, merchant
        )
        if error:
            raise serializers.ValidationError(error)

        if not user:
            return customer.user
        return user
