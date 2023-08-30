import random
import re
import string
from datetime import datetime, timedelta
from uuid import uuid4

from django.core.validators import RegexValidator

from users.models import BankAccount

# from core.resources.flutterwave import FlwAPI

# flw_api = FlwAPI


def parse_datetime(datetime_input):
    val = str(datetime_input)[:-6]
    parsed_datetime = datetime.fromisoformat(val)  # Removed the timezone offset
    return parsed_datetime.strftime("%B %d, %Y %I:%M%p")


def calculate_payment_amount_to_charge(amount, percent):
    try:
        amount = float(amount)
        amount_to_charge = amount + (amount * (percent / 100))
        return amount_to_charge
    except ValueError:
        return None


def convert_to_camel(snake_str):
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def generate_temp_id():
    return str(uuid4())


def generate_otp():
    return str(random.randint(100000, 999999))


def replace_space(file_name):
    return file_name.replace(" ", "_")


def minutes_to_seconds(minutes):
    return minutes * 60


def hours_to_seconds(hours):
    return minutes_to_seconds(hours * 60)


def days_to_seconds(days):
    return hours_to_seconds(days * 24)


def get_lga_by_state_alias(lga_map, state_alias):
    return lga_map.get(state_alias, None)


def generate_random_text(length):
    return "".join(
        random.choice("0123456789abcdefghijklmnopqrstuvwxyz") for i in range(length)
    )


def add_60_minutes():
    current_datetime = datetime.now()
    new_datetime = current_datetime + timedelta(minutes=60)
    formatted_datetime = new_datetime.strftime(
        "%Y-%m-%d %H:%M:%S"
    )  # Formats the datetime as "YYYY-MM-DD HH:MM:SS"
    return formatted_datetime


def generate_txn_reference():
    random_text = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    now = datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    hour = str(now.hour).zfill(2)
    minute = str(now.minute).zfill(2)
    second = str(now.second).zfill(2)

    txn_reference = random_text + year + month + day + hour + minute + second

    return txn_reference


def get_withdrawal_fee(amount):
    fee = amount * 0.02
    if amount <= 5000:
        charge = 10.75 + fee
    elif amount <= 50000:
        charge = 26.875 + fee
    else:
        charge = 53.75 + fee

    amount_payable = amount + charge
    return charge, amount_payable


def get_escrow_fees(amount):
    if amount < 100000:
        charge_percentage = 0.015  # 1.5%
    elif amount <= 500000:
        charge_percentage = 0.01  # 1%
    else:
        charge_percentage = 0.008  # 0.8%

    charge = amount * charge_percentage
    amount_payable = amount + charge

    return charge, amount_payable


def validate_bank_account(bank_code, account_number, user_id=None):
    existing_account = BankAccount.objects.filter(
        bank_code=bank_code, account_number=account_number
    ).first()

    if existing_account:
        return existing_account

    # is_valid = flw_api.validate_bank_account(bank_code, account_number)

    # if is_valid and is_valid["status"] == "success":
    #     new_bank_account = BankAccount.objects.create(
    #         user_id=user_id,
    #         bank_code=bank_code,
    #         account_number=account_number
    #     )
    #     return new_bank_account

    return None


CUSTOM_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # e.g "1993-12-25"
PHONE_NUMBER_SERIALIZER_REGEX_NGN = RegexValidator(
    regex=r"^\d{11}$", message="Phone number must be 11 digits only."
)
RECORD_NOT_FOUND_PAYLOAD = {
    "message": "Verification unsuccessful. Record not found!",
    "status": False,
    "payload": None,
}
EDIT_PROFILE_URL = "https://mybalanceapp.com/profile"
GET_STARTED_BUYER_URL = "https://mybalanceapp.com/buyer/dashboard"
GET_STARTED_SELLER_URL = "https://mybalanceapp.com/seller/dashboard"
RESET_PASSWORD_URL = "https://mybalanceapp.com/reset-password/"

TEST_NUBAN = "0234567890"
TEST_BANK_CODE = "035"

TEST_BVN = "22555299000"
TEST_NIN = "01234567890"

TEST_PASSPORT_NUMBER = "A00400000"
TEST_DRIVER_LICENSE_NUMBER = "AAD23208212298"
TEST_VOTER_CARD_NUMBER = "987f545AJ67890"
TEST_VOTER_STATE = "Lagos"
TEST_VOTER_LGA = "Ikeja"

TEST_FNAME = "John"
TEST_LNAME = "Doe"
TEST_DOB = "1993-11-03"
