from .base import FlutterwaveBaseService


class FlutterwaveService(FlutterwaveBaseService):
    @classmethod
    def initiate_bank_transfer(cls, data):
        url = f"{cls.FLW_BASE_URL}/charges?type=bank_transfer"
        return cls.make_post_request(
            url, data, camelize=False, flw_headers=cls.FLW_HEADERS
        )

    @classmethod
    def initiate_payout(cls, data):
        url = f"{cls.FLW_BASE_URL}/transfers"
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

    @classmethod
    def get_transfer_fee(cls, amount):
        url = f"{cls.FLW_BASE_URL}/transfers/fee?amount={amount}&currency=NGN"
        return cls.make_get_request(url, flw_headers=cls.FLW_HEADERS)

    @classmethod
    def validate_bank_account(cls, bank_code, account_number):
        url = f"{cls.FLW_BASE_URL}/accounts/resolve"
        data = {
            "account_number": account_number,
            "account_bank": bank_code,
        }
        return cls.make_post_request(
            url, data, camelize=False, flw_headers=cls.FLW_HEADERS
        )

    @classmethod
    def list_banks(cls):
        url = f"{cls.FLW_BASE_URL}/banks/NG"
        return cls.make_get_request(url, flw_headers=cls.FLW_HEADERS)
