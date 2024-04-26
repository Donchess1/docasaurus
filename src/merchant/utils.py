import datetime
import hashlib
import hmac
import time
from decimal import Decimal

import bcrypt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.cache import Cache
from core.resources.flutterwave import FlwAPI
from merchant.models import Customer, CustomerMerchant, Merchant
from users.models import UserProfile
from utils.utils import generate_random_text, generate_txn_reference

User = get_user_model()
cache = Cache()
flw_api = FlwAPI


def validate_request(request):
    api_key = request.headers.get("MerchantAPIKey")
    if not api_key:
        return [False, "Request Forbidden. API Key missing"]
    try:
        merchant = Merchant.objects.get(api_key=api_key)
        return [True, merchant]
    except Merchant.DoesNotExist:
        return [False, "Request Forbidden. Invalid API Key"]


def verify_otp(otp, temp_id):
    cache_data = cache.get(temp_id)
    if not cache_data or not cache_data["is_valid"]:
        return False, "OTP is invalid or expired!"

    if cache_data["otp"] != otp:
        return False, "Invalid OTP!"

    cache_data["is_valid"] = False
    cache.delete(temp_id)

    return True, cache_data


@transaction.atomic
def initiate_gateway_withdrawal_transaction(user, data):
    amount = data.get("amount")
    bank_code = data.get("bank_code")
    account_number = data.get("account_number")
    merchant_platform = data.get("merchant_platform_name")
    tx_ref = f"{generate_txn_reference()}_PMCKDU_1"
    description = "MyBalance Wallet Withdrawal"
    email = user.email

    txn = Transaction.objects.create(
        user_id=user,
        type="WITHDRAW",
        amount=amount,
        mode="MERCHANT_API",
        status="PENDING",
        reference=tx_ref,
        currency="NGN",
        provider="FLUTTERWAVE",
        meta={"title": "Wallet debit"},
    )
    # https://developer.flutterwave.com/docs/making-payments/transfers/overview/
    tx_data = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": int(amount),
        "narration": description,
        "reference": tx_ref,
        "currency": "NGN",
        "meta": {
            "amount_to_debit": amount,
            "customer_email": email,
            "tx_ref": tx_ref,
        },
        # "callback_url": f"{BACKEND_BASE_URL}/v1/shared/withdraw-callback",
    }

    obj = flw_api.initiate_payout(tx_data)
    msg = obj["message"]
    txn.meta.update({"description": f"FLW Transaction: {tx_ref}", "note": msg})
    txn.save()
    if obj["status"] == "error":
        return False, msg
    return (
        True,
        {"transaction_reference": tx_ref},
    )


def get_merchant_by_id(merchant_id):
    """
    Retrieve Merchant Instance by ID
    """
    try:
        instance = Merchant.objects.filter(id=merchant_id).first()
    except Exception as e:
        print("Error", str(e))
        instance = None
    return instance


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
        "mode": "MERCHANT_API",
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


def get_customer_merchant_instance(email, merchant):
    instance = None
    try:
        user = User.objects.filter(email=email).first()
        instance = CustomerMerchant.objects.filter(
            merchant=merchant, customer=user.customer
        ).first()
    except Exception as e:
        print("Error getting customer merchant_instance", str(e))
    return instance


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


def get_merchant_customer_transactions_by_customer_email(customer_email, merchant):
    merchant_transactions_queryset = Transaction.objects.filter(merchant=merchant)
    customer_queryset = merchant_transactions_queryset.filter(
        Q(escrowmeta__partner_email=customer_email)
        | Q(escrowmeta__meta__parties__buyer=customer_email)
        | Q(escrowmeta__meta__parties__seller=customer_email)
    ).distinct()
    locked_amount_subquery = LockedAmount.objects.filter(
        transaction=OuterRef("pk")
    ).values("transaction")
    customer_queryset = customer_queryset.annotate(
        has_locked_amount=Subquery(locked_amount_subquery)
    ).filter(has_locked_amount__isnull=False)

    return customer_queryset.filter(status="SUCCESSFUL", type="ESCROW")


def get_transaction_by_id(id):
    try:
        instance = Transaction.objects.get(id=id)
        return instance
    except Exception as e:
        print("Error getting transaction by id", str(e))
        return None


def check_transactions_are_valid_escrows(transactions):
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if transaction.type != "ESCROW":
            return False
    return True


def check_transactions_delivery_date_has_elapsed(transactions: list[str]) -> bool:
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if not transaction:
            continue
        delivery_date = transaction.escrowmeta.delivery_date
        if datetime.datetime.now().date() < delivery_date:
            return True
    return False


def check_transactions_already_unlocked(transactions):
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if transaction.status == "SETTLED":
            return False
    return True


def unlock_customer_escrow_transactions(transactions, user):
    for id in transactions:
        id = str(id)
        print("STARTUNG TO UNLOCK TRANSACTION with ID: " + id)
        try:
            txn = get_transaction_by_id(id)
            txn.status = "FUFILLED"
            txn.save()
            # Move amount from Buyer's Locked Balance to Unlocked Balance
            profile = user.userprofile
            profile.locked_amount -= Decimal(str(txn.amount))
            profile.unlocked_amount += int(txn.amount)

            # Evaluating free escrow transactions
            buyer_free_escrow_credits = int(profile.free_escrow_transactions)
            amount_to_credit_seller = int(txn.amount - txn.charge)
            seller = User.objects.filter(email=txn.lockedamount.seller_email).first()
            print("SELLER", seller)
            seller_charges = int(txn.charge)
            if buyer_free_escrow_credits > 0:
                # reverse charges to buyer wallet & deplete free credits
                profile.free_escrow_transactions -= 1
                profile.wallet_balance += int(txn.charge)
                tx_ref = generate_txn_reference()

                rev_txn = Transaction.objects.create(
                    user_id=user,
                    type="DEPOSIT",
                    amount=int(txn.charge),
                    status="SUCCESSFUL",
                    reference=tx_ref,
                    currency="NGN",
                    provider="MYBALANCE",
                    meta={
                        "title": "Wallet credit",
                        "description": "Free Escrow Reversal",
                    },
                )

            if seller.userprofile.free_escrow_transactions > 0:
                # credit full amount to seller and deplete free credits
                amount_to_credit_seller = int(txn.amount)
                seller_charges = 0
                seller.userprofile.free_escrow_transactions -= 1
                seller.userprofile.save()

            profile.save()
            instance = LockedAmount.objects.get(transaction=txn)

            # Credit amount to Seller's wallet balance after deducting applicable escrow fees
            seller = User.objects.get(email=instance.seller_email)
            seller_profile = seller.userprofile
            seller_profile.wallet_balance += int(amount_to_credit_seller)
            seller_profile.save()

            instance.status = "SETTLED"
            instance.save()

            # Notify Buyer & Seller that funds has been unlocked from escrow via email.
            # escrow_meta = txn.escrowmeta.meta
            # buyer_values = {
            #     "first_name": user.name.split(" ")[0],
            #     "recipient": user.email,
            #     "date": parse_datetime(txn.updated_at),
            #     "transaction_id": reference,
            #     "item_name": txn.meta["title"],
            #     "seller_name": seller.name,
            #     "bank_name": escrow_meta.get("bank_name"),
            #     "account_name": escrow_meta.get("account_name"),
            #     "account_number": escrow_meta.get("account_number"),
            #     "amount": f"NGN {add_commas_to_transaction_amount(txn.amount)}",
            # }
            # seller_values = {
            #     "first_name": seller.name.split(" ")[0],
            #     "recipient": seller.email,
            #     "date": parse_datetime(txn.updated_at),
            #     "transaction_id": reference,
            #     "item_name": txn.meta["title"],
            #     "buyer_name": user.name,
            #     "bank_name": escrow_meta.get("bank_name"),
            #     "account_name": escrow_meta.get("account_name"),
            #     "account_number": escrow_meta.get("account_number"),
            #     "amount": f"NGN {add_commas_to_transaction_amount(amount_to_credit_seller)}",
            #     "transaction_fee": f"N{seller_charges}",
            # }
            # tasks.send_unlock_funds_buyer_email(user.email, buyer_values)
            # tasks.send_unlock_funds_seller_email(seller.email, seller_values)

            # Create Notification for Buyer
            # UserNotification.objects.create(
            #     user=user,
            #     category="FUNDS_UNLOCKED_BUYER",
            #     title=notifications.FUNDS_UNLOCKED_BUYER_TITLE,
            #     content=notifications.FUNDS_UNLOCKED_BUYER_CONTENT,
            #     action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{reference}",
            # )

            # Create Notification for Seller
            # UserNotification.objects.create(
            #     user=seller,
            #     category="FUNDS_UNLOCKED_SELLER",
            #     title=notifications.FUNDS_UNLOCKED_CONFIRMATION_TITLE,
            #     content=notifications.FUNDS_UNLOCKED_CONFIRMATION_CONTENT,
            #     action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{reference}",
            # )
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
        print("FINISHED UNLOCKING TRANSACTION")


def generate_api_key(merchant_id):
    api_key = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        str(merchant_id).encode("utf-8") + time.ctime().encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    hashed_api_key = bcrypt.hashpw(api_key.encode("utf-8"), bcrypt.gensalt())
    return api_key, hashed_api_key.decode("utf-8")


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    return bcrypt.checkpw(api_key.encode("utf-8"), hashed_api_key.encode("utf-8"))
