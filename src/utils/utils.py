import random
import re
from uuid import uuid4

from django.core.validators import RegexValidator


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
