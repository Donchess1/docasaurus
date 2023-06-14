from .base import FlutterwaveBaseService


class FlutterwaveService(FlutterwaveBaseService):
    @classmethod
    def initiate_bank_transfer(cls, data):
        url = f"{cls.FLW_BASE_URL}/charges?type=bank_transfer"
        return cls.make_post_request(
            url, data, camelize=False, flw_headers=cls.FLW_HEADERS
        )

    @classmethod
    def initiate_payment_link(cls, data):
        url = f"{cls.FLW_BASE_URL}/payments"
        return cls.make_post_request(
            url, data, camelize=False, flw_headers=cls.FLW_HEADERS
        )

    @classmethod
    def verify_transaction(cls, transaction_id):
        url = f"{cls.FLW_BASE_URL}/transactions/{transaction_id}/verify"
        return cls.make_get_request(url, flw_headers=cls.FLW_HEADERS)
