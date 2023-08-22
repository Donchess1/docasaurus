import os

from utils.requests import Requests


class BaseThirdPartyService(Requests):
    Third_Party_API_URL = os.environ.get("THIRD_PARTY_API_URL")
    ZeehAfrica_API_URL = os.environ.get(
        "ZEEHAFRICA_PARTY_API_URL", "https://api.zeeh.africa/api/v1"
    )
