import os

from core.resources.flutterwave import FlwAPI
from core.resources.third_party.data.banks import BANKS
from core.resources.third_party.data.lga import LGAS
from core.resources.third_party.data.states import STATES
from core.resources.third_party.data.store import (
    BANK_ACCOUNT_DATA,
    BVN_DATA,
    DRIVER_LICENSE_DATA,
    NIN_DATA,
    PASSPORT_DATA,
    VOTER_CARD_DATA,
)
from users.models.bank_account import BankAccount
from users.serializers.bank_account import BankAccountSerializer
from utils.utils import (
    RECORD_NOT_FOUND_PAYLOAD,
    TEST_BANK_CODE,
    TEST_BVN,
    TEST_DOB,
    TEST_DRIVER_LICENSE_NUMBER,
    TEST_FNAME,
    TEST_LNAME,
    TEST_NIN,
    TEST_NUBAN,
    TEST_PASSPORT_NUMBER,
    TEST_VOTER_CARD_NUMBER,
    TEST_VOTER_LGA,
    TEST_VOTER_STATE,
    get_lga_by_state_alias,
)

from .base import BaseThirdPartyService

# ENVIRONMENT = os.environ.get("ENVIRONMENT")
ENVIRONMENT = "staging"


class ThirdPartyAPI(BaseThirdPartyService):
    @classmethod
    def validate_BVN(cls, number):
        if number != TEST_BVN:
            return RECORD_NOT_FOUND_PAYLOAD
        return {
            "message": "Verification Successful",
            "status": True,
            "payload": BVN_DATA,
        }
        url = f"{cls.Third_Party_API_URL}/bvn"
        json_data = {"bvn": number}
        return cls.make_post_request(url, json_data)

    @classmethod
    def validate_NIN(cls, number):
        if number != TEST_NIN:
            return RECORD_NOT_FOUND_PAYLOAD
        return {
            "message": "Verification Successful",
            "status": True,
            "payload": NIN_DATA,
        }
        url = f"{cls.Third_Party_API_URL}/nin"
        json_data = {"bvn": number}
        return cls.make_post_request(url, json_data)

    @classmethod
    def validate_voters_card(cls, data):
        vc_number = data.get("number", None)
        first_name = data.get("first_name", None)
        last_name = data.get("last_name", None)
        state = data.get("state", None)
        lga = data.get("lga", None)
        dob = data.get("dob", None)

        if (
            vc_number == TEST_VOTER_CARD_NUMBER
            and first_name == TEST_FNAME
            and last_name == TEST_LNAME
            and state == TEST_VOTER_STATE
            and lga == TEST_VOTER_LGA
            and dob == TEST_DOB
        ):
            return {
                "message": "Verification Successful",
                "status": True,
                "payload": VOTER_CARD_DATA,
            }
        return RECORD_NOT_FOUND_PAYLOAD

        url = f"{cls.Third_Party_API_URL}/verify/VoterCard"
        json_data = {"vc_number": vc_number, "last_name": last_name, "state": state}

        return cls.make_post_request(url, json_data)

    @classmethod
    def validate_driver_license(cls, data):
        card_number = data.get("card_number", None)
        dob = data.get("dob", None)

        if card_number == TEST_DRIVER_LICENSE_NUMBER and dob == TEST_DOB:
            return {
                "message": "Verification Successful",
                "status": True,
                "payload": DRIVER_LICENSE_DATA,
            }
        return RECORD_NOT_FOUND_PAYLOAD

        url = f"{cls.Third_Party_API_URL}/verify/DriverCard"
        json_data = {"card_number": card_number, "dob": dob}
        return cls.make_post_request(url, json_data)

    @classmethod
    def validate_international_passport(cls, data):
        passport_number = data["number"]
        last_name = data["last_name"]

        if passport_number == TEST_PASSPORT_NUMBER and last_name == TEST_LNAME:
            return {
                "message": "Verification Successful",
                "status": True,
                "payload": PASSPORT_DATA,
            }
        return RECORD_NOT_FOUND_PAYLOAD

        url = f"{cls.Third_Party_API_URL}/verify/NationalPassport"
        json_data = {
            "passport_number": passport_number,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
        }

        return cls.make_post_request(url, json_data)

    @classmethod
    def validate_bank_account(cls, bank_code, account_number):
        if ENVIRONMENT == "staging":
            if account_number == TEST_NUBAN and bank_code == TEST_BANK_CODE:
                return {
                    "message": "Account details fetched",
                    "status": True,
                    "data": BANK_ACCOUNT_DATA,
                }
            return RECORD_NOT_FOUND_PAYLOAD
        return FlwAPI.validate_bank_account(bank_code, account_number)

    @classmethod
    def list_banks(cls, read_from_file=False):
        return FlwAPI.list_banks()

    @classmethod
    def list_states(cls):
        return {
            "message": "NGN States fetched successfully",
            "status": True,
            "payload": STATES,
        }

    @classmethod
    def list_lgas_by_state_alias(cls, alias=None):
        obj = get_lga_by_state_alias(LGAS, alias)
        if not obj:
            return {
                "message": "State alias not found",
                "status": False,
                "payload": None,
            }
        return {
            "message": "LGAs fetched successfully",
            "status": True,
            "payload": obj,
        }
