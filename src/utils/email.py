import os

from email_validator import EmailNotValidError, validate_email

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


def validate_email_address(email: str, check_deliverability=False):
    # REF: https://pypi.org/project/email-validator/
    is_valid, message, validated_response = False, "", {}

    if env == "live" and "+" in email:
        message = (
            "Invalid character '+' now allowed. Please enter a valid email address."
        )
        return is_valid, message, validated_response

    try:
        # this checks that the email address is valid.
        # we turn on check_deliverability for first-time validations like on registration or escrow initiation creation
        # but not on login pages. No need to resolve DNS everywhere.
        obj = validate_email(email, check_deliverability=check_deliverability)
        # After this point, we use only the normalized form of the email address,
        # especially before going to a database query.
        validated_response = {
            "normalized_email": obj.normalized,
            "ascii_email": obj.ascii_email if obj.ascii_email else None,
            "local_part": obj.local_part if obj.local_part else None,
            "ascii_domain": obj.ascii_domain if obj.ascii_domain else None,
        }
        message = "Validation successful!"
        is_valid = True
    except EmailNotValidError as e:
        print("Error occurred while validating email ===>", str(e))
        message = f"Invalid email. {str(e)}"

    return is_valid, message, validated_response
