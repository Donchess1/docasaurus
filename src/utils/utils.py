import os
import random
import re
import string
from datetime import datetime, timedelta
from uuid import uuid4

from django.core.validators import RegexValidator


def parse_datetime(datetime_input):
    val = str(datetime_input)[:-6]
    parsed_datetime = datetime.fromisoformat(val)  # Removed the timezone offset
    parsed_datetime += timedelta(hours=1)  # Offset by an hour ahead
    return parsed_datetime.strftime("%B %d, %Y %I:%M%p")


def parse_date(date_input):
    # Convert date to string
    val = str(date_input)
    parsed_date = datetime.fromisoformat(val)
    day = parsed_date.strftime("%d").lstrip("0")  # Remove leading zero
    month = parsed_date.strftime("%b.")
    year = parsed_date.strftime("%Y")

    # Add appropriate suffix to the day
    if day.endswith("1") and day != "11":
        suffix = "st"
    elif day.endswith("2") and day != "12":
        suffix = "nd"
    elif day.endswith("3") and day != "13":
        suffix = "rd"
    else:
        suffix = "th"

    formatted_date = f"{month} {day}{suffix} {year}"
    return formatted_date


def custom_flatten_uuid(uuid_string):
    """Flatten a UUID string by removing dashes and reverses the string."""
    return uuid_string.replace("-", "")[::-1]


def unflatten_uuid(flattened_uuid):
    flattened_uuid = flattened_uuid[::-1]
    """Deflatten a flattened UUID string by reversing the string and adding dashes."""
    return "-".join(
        [
            flattened_uuid[:8],
            flattened_uuid[8:12],
            flattened_uuid[12:16],
            flattened_uuid[16:20],
            flattened_uuid[20:],
        ]
    )


def add_commas_to_transaction_amount(number):
    number = str(number)
    # Round the number to 2 decimal places
    number = round(float(number), 2)
    # Split the number into integer and decimal parts
    integer_part, decimal_part = str(number).split(".")
    # Reverse the integer part
    reversed_int = integer_part[::-1]
    # Initialize variables
    result = ""
    count = 0
    # Iterate through the reversed string
    for char in reversed_int:
        result = char + result
        count += 1
        # Add comma after every third character, except for the last group
        if count % 3 == 0 and count != len(reversed_int):
            result = "," + result
    # Add the decimal part back, ensuring it has 2 digits
    result = f"{result}.{decimal_part.zfill(2)}"
    return result


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


def generate_short_uuid():
    new_uuid = generate_temp_id()
    return new_uuid.split("-")[0][:-4] + generate_random_text(20)


api_key_prefix = (
    "live" if os.environ.get("ENVIRONMENT", None) == "production" else "test"
)


def get_pub_key():
    return "{}_{}".format(f"{api_key_prefix}_pub", generate_short_uuid())


def get_priv_key():
    return "{}_{}".format(f"{api_key_prefix}_priv", generate_short_uuid())


MODES = ["LIVE", "TEST"]


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


def generate_txn_reference():
    random_text = "".join(random.choices(string.ascii_uppercase + string.digits, k=9))

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
    # fee = amount * 0.02
    if amount <= 5000:
        # charge = 10.75 + fee
        charge = 10.75
    elif amount <= 50000:
        # charge = 26.875 + fee
        charge = 26.875
    else:
        # charge = 53.75 + fee
        charge = 53.75

    charge = 0  # temporarily disable withdrawal fee
    amount_payable = amount + charge
    return charge, amount_payable


def get_escrow_fees(amount):
    if amount < 100000:
        charge_percentage = 0.015  # 1.5%
    elif amount <= 500000:
        charge_percentage = 0.01  # 1%
    else:
        charge_percentage = 0.008  # 0.8%
    
    charge_percentage = 0 # temporarily disable escrow fee

    charge = amount * charge_percentage
    amount_payable = amount + charge

    return charge, amount_payable


def format_rejected_reasons(rejected_reasons):
    if not rejected_reasons:
        return ""

    if len(rejected_reasons) == 1:
        return rejected_reasons[0].replace("_", " ").title()

    elif len(rejected_reasons) == 2:
        return f"{rejected_reasons[0].replace('_', ' ').title()} & {rejected_reasons[1].replace('_', ' ').title()}"

    else:
        formatted_reasons = ", ".join(
            reason.replace("_", " ").title() for reason in rejected_reasons[:-1]
        )
        return f"{formatted_reasons} & {rejected_reasons[-1].replace('_', ' ').title()}"


CUSTOM_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # e.g "1993-12-25"
PHONE_NUMBER_SERIALIZER_REGEX_NGN = RegexValidator(
    regex=r"^\d{11}$", message="Phone number must be 11 digits only."
)
RECORD_NOT_FOUND_PAYLOAD = {
    "message": "Invalid bank details.",
    "status": False,
    "data": None,
}

FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
EDIT_PROFILE_URL = f"{FRONTEND_BASE_URL}/profile"
GET_STARTED_BUYER_URL = f"{FRONTEND_BASE_URL}/buyer/dashboard"
GET_STARTED_SELLER_URL = f"{FRONTEND_BASE_URL}/seller/dashboard"
RESET_PASSWORD_URL = f"{FRONTEND_BASE_URL}/reset-password"

TEST_BANK_CODE_1 = "035"
TEST_NUBAN_1 = "0234567890"
TEST_BANK_CODE_2 = "044"
TEST_NUBAN_2 = "0690000040"

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

CURRENCIES = ["NGN", "USD"]
MINIMUM_WALLET_DEPOSIT_AMOUNT = 500
MINIMUM_ESCROW_TOPUP_AMOUNT = 100
