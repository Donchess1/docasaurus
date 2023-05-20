from .base import FlutterwaveBaseService


class FlutterwaveService(FlutterwaveBaseService):
    @classmethod
    def initiate_bank_transfer(cls, data):
        url = f"{cls.FLW_BASE_URL}/charges?type=bank_transfer"
        return cls.make_post_request(
            url, data, camelize=False, flw_headers=cls.FLW_HEADERS
        )
