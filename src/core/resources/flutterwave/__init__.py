from .main import FlutterwaveService


class FlwAPI(FlutterwaveService):
    pass

# Reference: https://developer.flutterwave.com/docs/collecting-payments/standard
# session_duration (optional): The duration (minutes) that the session should remain valid for.
# The maximum possible value is 1440 minutes (24 hours).

# max_retry_attempt (optional): This allows you to set the maximum number of times
# that a customer can retry after a failed transaction before the checkout is closed.


FLW_PAYMENT_CONFIGURATION = {
        "session_duration": 7,  
        "max_retry_attempt": 1,
    }

FLW_PAYMENT_CUSTOMIZATION = {
                "title": "MyBalance",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            }