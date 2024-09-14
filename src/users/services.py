import re

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from business.models.business import Business
from business.serializers.business import BusinessSerializer
from console.models.transaction import Transaction
from core.resources.jwt_client import JWTClient
from merchant.utils import get_merchant_by_email
from users.models.bank_account import BankAccount
from users.models.kyc import UserKYC
from users.models.profile import UserProfile
from users.serializers.bank_account import BankAccountSerializer
from users.serializers.kyc import UserKYCSerializer
from users.serializers.profile import UserProfileSerializer
from users.serializers.user import UserSerializer

User = get_user_model()


def get_user_profile_data(user: User) -> dict:
    user_profile: UserProfile = user.userprofile

    bank_account = user_profile.bank_account_id
    kyc = user_profile.kyc_id
    business = user_profile.business_id
    banks = BankAccount.objects.filter(user_id=user)

    queryset = Transaction.objects.filter(
        Q(type="ESCROW") & Q(status="PENDING") & Q(escrowmeta__partner_email=user.email)
    ).order_by("-created_at")
    pending_escrows = [transaction.reference for transaction in queryset]

    serializer = UserProfileSerializer(user_profile)
    ser_data = dict(serializer.data)

    del ser_data["bank_account_id"]
    del ser_data["kyc_id"]
    del ser_data["business_id"]
    ser_data["full_name"] = (user.name).upper()
    ser_data["phone_number"] = user.phone
    ser_data["email"] = user.email
    ser_data["pending_escrows"] = pending_escrows

    data = {
        **ser_data,
        "bank_account": BankAccountSerializer(bank_account).data
        if bank_account
        else None,
        "kyc": UserKYCSerializer(kyc).data if kyc else None,
        "business": BusinessSerializer(business).data if business else None,
        "bank_accounts": BankAccountSerializer(banks, many=True).data,
    }

    return data


def handle_successful_login(user: User) -> dict:
    profile = user.userprofile
    profile.last_login_date = timezone.now()
    # validate phone number - flag 02000000000 - 02000000099
    # this was used to temporarily force duplicate numbers to be overwritten with a range of numbers
    # TODO: remove this after we have cleaned up the DB with fake numbers
    # after prompting people to change their numbers
    phone_number = user.phone
    phone_pattern = re.compile(r"^020000000\d{2}$")
    profile.phone_number_flagged = True if phone_pattern.match(phone_number) else False
    profile.save()

    token = JWTClient.sign(user.id)
    merchant = get_merchant_by_email(user.email)

    data = {
        "token": token["access_token"],
        "phone_number_flagged": profile.phone_number_flagged,
        "user": UserSerializer(user).data,
        "merchant": str(merchant.id) if merchant else None,
        "role": None,
        "permissions": [],
    }

    return data
