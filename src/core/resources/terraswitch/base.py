import os

from utils.requests import Requests


class TerraSwitchBaseService(Requests):
    TERRASWITCH_BASE_URL = os.environ.get("TERRASWITCH_BASE_URL")
    TERRASWITCH_SECRET_KEY = os.environ.get("TERRASWITCH_SECRET_KEY")
    TERRASWITCH_PIN = os.environ.get("TERRASWITCH_PIN")
    TERRASWITCH_HEADERS = {
        "Authorization": f"Bearer {TERRASWITCH_SECRET_KEY}",
        "Content-Type": "application/json",
        "lg": "en",
        "ch": "web",
    }
