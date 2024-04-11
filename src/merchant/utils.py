from django.contrib.auth import get_user_model

from merchant.models import Customer, CustomerMerchant, Merchant
from users.models import UserProfile
from utils.utils import generate_random_text

User = get_user_model()


def validate_request(request):
    api_key = request.headers.get("API-KEY")
    if not api_key:
        return [False, "Request Forbidden. API Key missing"]
    try:
        merchant = Merchant.objects.get(api_key=api_key)
        return [True, merchant]
    except Merchant.DoesNotExist:
        return [False, "Request Forbidden. Invalid API Key"]


def customer_phone_numer_exists_for_merchant(merchant, phone_number):
    """
    Checks if there is an exisitng customer with the phone number linked to a merchant
    """
    instance = CustomerMerchant.objects.filter(
        merchant=merchant, alternate_phone_number=phone_number
    ).first()
    return True if instance else False


def customer_with_email_exists_for_merchant(merchant, user):
    """
    Checks if there is an exisitng customer with the email linked to a merchant
    """
    if Customer.objects.filter(user=user).first():
        instance = CustomerMerchant.objects.filter(
            merchant=merchant, customer=user.customer
        ).first()
        return True if instance else False
    return False


def create_customer_user_instance_for_merchant(
    customer, merchant, phone_number, name, email, customer_type
):
    CustomerMerchant.objects.create(
        customer=customer,
        merchant=merchant,
        alternate_phone_number=phone_number,
        alternate_name=name,
        user_type=customer_type,
        name_match=True if name == customer.user.name else False,
        user_type_match=True
        if customer_type == customer.user.userprofile.user_type
        else False,
        phone_number_match=True if phone_number == customer.user.phone else False,
    )


def create_or_update_customer_user(email, phone_number, name, customer_type, merchant):
    """
    Creates or updates a customer with the given email, phone number & customer type.
    """
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        customer, created = Customer.objects.get_or_create(user=existing_user)
        create_customer_user_instance_for_merchant(
            customer, merchant, phone_number, name, email, customer_type
        )
        return existing_user, customer, None
    else:
        user_data = {
            "email": email,
            "phone": phone_number,
            "name": name,
            "password": generate_random_text(15),
            f"is_{customer_type.lower()}": True,
        }
        # TODO: Notify the user via email to setup their password
        user = User.objects.create_user(**user_data)
        profile_data = UserProfile.objects.create(
            user_id=user,
            user_type=customer_type,
            free_escrow_transactions=10 if customer_type == "SELLER" else 5,
        )
        customer = Customer.objects.create(user=user)
        create_customer_user_instance_for_merchant(
            customer, merchant, phone_number, name, email, customer_type
        )
        return user, customer, None
