import os

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


def validate_email_body(value):
    if env == "live" and "+" in value:
        return [True, "Invalid email address. Cannot contain '+'"]
    else:
        return [False, None]
