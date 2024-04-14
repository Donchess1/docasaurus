from django.contrib.auth import get_user_model

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from merchant.models import Customer, CustomerMerchant, Merchant
from users.models import UserProfile
from utils.utils import generate_random_text, generate_txn_reference

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


def get_merchant_customers_by_user_type(merchant, user_type):
    return [
        customer.user.email
        for customer in merchant.customer_set.all()
        if CustomerMerchant.objects.filter(
            customer=customer, merchant=merchant, user_type=user_type
        ).exists()
    ]


def check_escrow_user_is_valid(email, merchant_customer_type_list):
    return True if email in merchant_customer_type_list else False


def create_merchant_escrow_transaction(
    merchant,
    buyer,
    seller,
    charge,
    amount,
    purpose,
    title,
    tx_ref,
    item_type,
    item_quantity,
    delivery_date,
):
    transaction_data = {
        "user_id": merchant.user_id,
        "status": "PENDING",
        "type": "ESCROW",
        "provider": "MYBALANCE",
        "mode": "WEB",
        "merchant": merchant,
        "amount": amount,
        "charge": charge,
        "meta": {"title": title, "description": purpose},
        "reference": tx_ref,
        "provider_tx_reference": tx_ref,
    }
    transaction = Transaction.objects.create(**transaction_data)

    escrow_meta_data = {
        "author": "MERCHANT",
        "transaction_id": transaction,
        "partner_email": buyer,
        "purpose": purpose,
        "item_type": item_type,
        "item_quantity": item_quantity,
        "delivery_date": delivery_date,
        "delivery_tolerance": 3,
        "meta": {"parties": {"buyer": buyer, "seller": seller}},
    }
    escrow_meta = EscrowMeta.objects.create(**escrow_meta_data)
    return transaction


def generate_deposit_transaction_for_escrow(escrow_txn, buyer, amount, tx_ref):
    email = buyer.email

    deposit_txn = Transaction.objects.create(
        user_id=buyer,
        type="DEPOSIT",
        amount=amount,
        status="PENDING",
        reference=tx_ref,
        currency="NGN",
        provider="FLUTTERWAVE",
        meta={"title": "Escrow transaction fund"},
    )

    return deposit_txn


def get_escrow_transaction_users_for_merchant(
    escrow_txn, buyer_email, seller_email, amount
):
    return {"buyer": buyer, "seller": seller}


def get_customer_merchant_instance(email, merchant):
    user = User.objects.filter(email=email).first()
    return CustomerMerchant.objects.filter(
        merchant=merchant, customer=user.customer
    ).first()


def get_merchant_escrow_users(escrow_txn, merchant):
    meta = escrow_txn.escrowmeta.meta
    if not meta:
        return None
    transaction_parties = meta.get("parties")
    buyer_email = transaction_parties.get("buyer")
    seller_email = transaction_parties.get("seller")

    return {
        "buyer": get_customer_merchant_instance(buyer_email, merchant),
        "seller": get_customer_merchant_instance(seller_email, merchant),
    }
