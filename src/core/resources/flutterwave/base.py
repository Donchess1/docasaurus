import os

from utils.requests import Requests


class FlutterwaveBaseService(Requests):
    FLW_BASE_URL = os.environ.get("FLW_BASE_URL")
    FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY")
    FLW_HEADERS = {"Authorization": FLW_SECRET_KEY, "Content-Type": "application/json"}
