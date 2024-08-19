import stripe
from django.conf import settings


class StripeService:
    stripe.api_key = settings.STRIPE_SECRET_KEY

    @classmethod
    def create_checkout_session(
        cls, amount, currency="usd", success_url=None, cancel_url=None, customer_id=None, metadata=None
    ):
        """
        Create a checkout session for redirecting the user to Stripe's hosted checkout page.
        """
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": "Test Product",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer_id,
            metadata=metadata,
        )
        return session

    @classmethod
    def get_or_create_customer(cls, email, name):
        """
        Retrieve an existing Stripe customer or create a new one if it doesn't exist.
        """
        customers = stripe.Customer.list(email=email).data
        if customers:
            return customers[0]
        else:
            customer = stripe.Customer.create(email=email, name=name)
            return customer

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
