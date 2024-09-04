from .base import TerraSwitchBaseService


class TerraSwitchService(TerraSwitchBaseService):
    @classmethod
    def get_corporate_account_details(cls):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/account"
        return cls.make_get_request(url, terraswitch_headers=cls.TERRASWITCH_HEADERS)

    @classmethod
    def get_linked_corporate_banks(cls):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/banks"
        return cls.make_get_request(url, terraswitch_headers=cls.TERRASWITCH_HEADERS)

    @classmethod
    def get_wallet_details(cls):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/wallet"
        return cls.make_get_request(url, terraswitch_headers=cls.TERRASWITCH_HEADERS)

    @classmethod
    def get_wallet_transactions(cls, limit=50, page=1, order="desc"):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/wallet-transactions?limit={limit}&page={page}&order={order}"
        return cls.make_get_request(url, terraswitch_headers=cls.TERRASWITCH_HEADERS)

    @classmethod
    def get_wallet_details(cls):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/wallet"
        return cls.make_get_request(url, terraswitch_headers=cls.TERRASWITCH_HEADERS)

    @classmethod
    def initiate_payment_link(cls, data):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/initialize"
        return cls.make_post_request(
            url, data, camelize=False, terraswitch_headers=cls.TERRASWITCH_HEADERS
        )

    @classmethod
    def initiate_payout(cls, data):
        data["pin"] = cls.TERRASWITCH_PIN
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/transfer"
        return cls.make_post_request(
            url, data, camelize=False, terraswitch_headers=cls.TERRASWITCH_HEADERS
        )

    @classmethod
    def verify_transaction(cls, transaction_ref):
        url = f"{cls.TERRASWITCH_BASE_URL}/terra/v1/corporate/verify-transaction"
        data = {
            "reference": transaction_ref,
        }
        return cls.make_post_request(
            url, data, camelize=False, terraswitch_headers=cls.TERRASWITCH_HEADERS
        )

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
