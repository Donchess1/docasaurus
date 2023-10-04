import os

from utils.requests import Requests


class ZeehAfricaServiceBaseService(Requests):
    ZEEHAFRICA_BASE_URL = os.environ.get("ZEEHAFRICA_BASE_URL")
    ZEEHAFRICA_PUBLIC_KEY = os.environ.get("ZEEHAFRICA_PUBLIC_KEY")
    ZEEHAFRICA_PRIVATE_KEY = os.environ.get("ZEEHAFRICA_PRIVATE_KEY")
    ZEEHAFRICA_HEADERS = {
        "zeeh-private-key": ZEEHAFRICA_PRIVATE_KEY,
        "Content-Type": "application/json",
    }
