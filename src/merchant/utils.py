import datetime
import hashlib
import hmac
import os
import time
from decimal import Decimal
from uuid import UUID

import bcrypt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from core.resources.cache import Cache
from core.resources.flutterwave import FlwAPI
from merchant import tasks
from merchant.models import ApiKey, Customer, CustomerMerchant, Merchant, PayoutConfig
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from users.models import UserProfile
from utils.activity_log import log_transaction_activity
from utils.text import notifications
from utils.utils import (
    add_commas_to_transaction_amount,
    generate_random_text,
    generate_txn_reference,
    get_escrow_fees,
    parse_date,
    parse_datetime,
)

User = get_user_model()
cache = Cache()
flw_api = FlwAPI
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
MINIMUM_WITHDRAWAL_AMOUNT = 100


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
    cache_data = None
    with Cache() as cache:
        cache_data = cache.get(temp_id)
    if not cache_data or not cache_data["is_valid"]:
        return False, "OTP is invalid or expired!"

    if cache_data["otp"] != otp:
        return False, "Invalid OTP!"

    cache_data["is_valid"] = False
    with Cache() as cache:
        cache.delete(temp_id)

    return True, cache_data


def verify_merchant_widget_token_key(key):
    cache_data = None
    with Cache() as cache:
        cache_data = cache.get(key)
    if not cache_data or not cache_data["is_valid"]:
        return False, "Widget session is invalid or expired!"

    # cache_data["is_valid"] = False
    # cache.delete(key)
    return True, cache_data


@transaction.atomic
def initiate_gateway_withdrawal_transaction(user, data, request_meta, initiator):
    amount = data.get("amount")
    bank_code = data.get("bank_code")
    account_number = data.get("account_number")
    merchant_id = data.get("merchant_id")
    merchant = get_merchant_by_id(merchant_id)
    currency = data.get("currency", "NGN")
    tx_ref = f"{generate_txn_reference()}_PMCKDU_1"
    description = "MyBalance TRF-API"
    email = user.email
    customer_name = data.get("customer_name")

    txn = Transaction.objects.create(
        user_id=user,
        type="WITHDRAW",
        amount=amount,
        mode="MERCHANT_API",
        status="PENDING",
        reference=tx_ref,
        merchant=merchant,
        currency=currency,
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
        "currency": currency,
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

    description = f"{(customer_name).upper()} initiated withdrawal of {currency} {add_commas_to_transaction_amount(amount)} from wallet. Initiator: {initiator}"
    log_transaction_activity(txn, description, request_meta)

    _, wallet = user.get_currency_wallet(txn.currency)
    description = f"Previous User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(txn, description, request_meta)

    user.debit_wallet(amount, txn.currency)

    _, wallet = user.get_currency_wallet(txn.currency)
    description = f"Updated User Balance after Init Debit of {txn.currency} {add_commas_to_transaction_amount(amount)}: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(txn, description, request_meta)

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
        print("Error retrieving Merchant", str(e))
        instance = None
    return instance


def get_merchant_users_redirect_url(merchant: Merchant) -> dict:
    """
    Retrieve Merchant Redicrect URLs for Buyer and Seller
    """
    try:
        instance = ApiKey.objects.filter(merchant=merchant).first()
        if instance:
            return {
                "buyer_redirect_url": instance.buyer_redirect_url,
                "seller_redirect_url": instance.seller_redirect_url,
            }
    except Exception as e:
        print("Error retrieving Merchant Redirect URLs", str(e))
        return None


def get_merchant_by_email(email):
    """
    Retrieve Merchant Instance by email
    """
    try:
        user = User.objects.filter(email=email).first()
        instance = Merchant.objects.filter(user_id=user).first()
    except Exception as e:
        print("Error", str(e))
        instance = None
    return instance


def get_merchant_active_payout_configuration(merchant: Merchant) -> PayoutConfig:
    """
    Retrieve Merchant Payout configuration
    """
    try:
        instance = PayoutConfig.objects.filter(
            merchant=merchant, is_active=True
        ).first()
    except Exception as e:
        instance = None
    return instance


def calculate_percentage_charge(amount, payout_config_value):
    return (amount * payout_config_value) / 100


def get_merchant_transaction_charges(
    merchant: Merchant, amount: int, payout_config: PayoutConfig
) -> dict:
    """
    Retrieve Merchant Payout for escrow amount
    """
    charges = {}
    for role, payment_type, amount_field in [
        ("buyer", payout_config.buyer_charge_type, "buyer_amount"),
        ("seller", payout_config.seller_charge_type, "seller_amount"),
    ]:
        if payment_type == "NO_FEES":
            charges[f"{role}_charge"] = 0
        elif payment_type == "FLAT_FEE":
            payout_config_value = getattr(payout_config, amount_field)
            charges[f"{role}_charge"] = payout_config_value
        else:
            payout_config_value = getattr(payout_config, amount_field)
            charge = calculate_percentage_charge(amount, payout_config_value)
            charges[f"{role}_charge"] = charge
    return charges


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
        existing_user.create_wallet()
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
            "is_buyer": True if customer_type in ("BUYER", "CUSTOM") else False,
            "is_seller": True if customer_type in ("SELLER", "CUSTOM") else False,
        }
        # TODO: Notify the user via email to setup their password
        user = User.objects.create_user(**user_data)
        user.create_wallet()
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


def get_merchant_customers_email_addresses(merchant) -> [str]:
    return [
        customer.user.email
        for customer in merchant.customer_set.all()
        if CustomerMerchant.objects.filter(
            customer=customer,
            merchant=merchant,
        ).exists()
    ]


def escrow_user_is_valid(email, merchant_customer_type_list):
    return True if email in merchant_customer_type_list else False


def notify_seller_escrow_transaction_via_email(
    seller: CustomerMerchant,
    buyer: CustomerMerchant,
    merchant: Merchant,
    escrow_txn: Transaction,
):
    escrow_amount = add_commas_to_transaction_amount(escrow_txn.amount)
    seller_values = {
        "date": parse_datetime(escrow_txn.updated_at),
        "amount_funded": f"{escrow_txn.currency} {escrow_amount}",
        "transaction_id": f"{(escrow_txn.reference).upper()}",
        "item_name": escrow_txn.meta.get("title"),
        "delivery_date": parse_date(escrow_txn.escrowmeta.delivery_date),
        "buyer_name": buyer.alternate_name,
        "buyer_phone": buyer.alternate_phone_number,
        "buyer_email": buyer.customer.user.email,
        "merchant_platform": merchant.name,
    }
    txn_tasks.send_lock_funds_merchant_seller_email.delay(
        seller.customer.user.email, seller_values
    )
    # Create Notification for Seller
    UserNotification.objects.create(
        user=seller.customer.user,
        category="FUNDS_LOCKED_SELLER",
        title=notifications.FundsLockedSellerNotification(
            escrow_amount, escrow_txn.currency
        ).TITLE,
        content=notifications.FundsLockedSellerNotification(
            escrow_amount, escrow_txn.currency
        ).CONTENT,
        action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn.reference}",
    )


def notify_merchant_escrow_transaction_via_email(
    seller: CustomerMerchant,
    buyer: CustomerMerchant,
    merchant: Merchant,
    escrow_txn: Transaction,
):
    merchant_values = {
        "date": parse_datetime(escrow_txn.updated_at),
        "amount_funded": f"NGN {add_commas_to_transaction_amount(str(escrow_txn.amount))}",
        "transaction_id": (escrow_txn.reference).upper(),
        "item_name": escrow_txn.meta["title"],
        "delivery_date": parse_date(escrow_txn.escrowmeta.delivery_date),
        "seller_name": seller.alternate_name,
        "seller_phone": seller.alternate_phone_number,
        "seller_email": seller.customer.user.email,
        "buyer_name": buyer.alternate_name,
        "buyer_phone": buyer.alternate_phone_number,
        "buyer_email": buyer.customer.user.email,
        "merchant_platform": escrow_txn.merchant.name,
    }
    txn_tasks.send_lock_funds_merchant_email.delay(
        merchant.user_id.email, merchant_values
    )


@transaction.atomic
def create_merchant_escrow_transaction(
    merchant: Merchant,
    buyer_email: str,
    seller_email: str,
    item: dict,
    source: Transaction,
    payout_config: PayoutConfig,
    currency: str,
    request_meta: dict,
):
    title = item.get("title")
    description = item.get("description")
    category = item.get("category")
    item_quantity = item.get("item_quantity")
    delivery_date = item.get("delivery_date")
    amount = item.get("amount")
    charge, amount_payable = get_escrow_fees(amount)
    tx_ref = generate_txn_reference()

    transaction_data = {
        "user_id": merchant.user_id,
        "status": "SUCCESSFUL",
        "type": "ESCROW",
        "provider": "MYBALANCE",
        "mode": "MERCHANT_API",
        "merchant": merchant,
        "currency": currency,
        "amount": int(amount),
        "charge": int(charge),
        "meta": {
            "title": title,
            "description": description,
            "category": category,
            "source_payment_transaction": str(source),
        },
        "reference": tx_ref,
        "provider_tx_reference": tx_ref,
    }
    escrow_txn = Transaction.objects.create(**transaction_data)

    escrow_meta_data = {
        "author": "MERCHANT",
        "transaction_id": escrow_txn,
        "partner_email": buyer_email,
        "purpose": description,
        "item_type": title,
        "item_quantity": item_quantity,
        "delivery_date": delivery_date,
        "delivery_tolerance": 3,
        "payout_config": payout_config,
        "parent_payment_transaction": source,
        "meta": {"parties": {"buyer": buyer_email, "seller": seller_email}},
    }
    escrow_txn_meta = EscrowMeta.objects.create(**escrow_meta_data)

    buyer: CustomerMerchant = get_customer_merchant_instance(buyer_email, merchant)
    seller: CustomerMerchant = get_customer_merchant_instance(seller_email, merchant)
    locked_amount = LockedAmount.objects.create(
        transaction=escrow_txn,
        user=buyer.customer.user,
        seller_email=seller_email,
        amount=escrow_txn.amount,
        status="ESCROW",
    )

    seller.customer.user.update_locked_amount(
        amount=escrow_txn.amount,
        currency=escrow_txn.currency,
        mode="INWARD",
        type="CREDIT",
    )
    # Buyer locked amount has already been updated before this function call.

    description = f"{(merchant.name).upper()} <{merchant.user_id.email}> [MERCHANT] successfully initiated escrow worth {escrow_txn.currency} {add_commas_to_transaction_amount(escrow_txn.amount)} for RECEIPIENT/BUYER {(buyer.alternate_name).upper()} <{buyer.customer.user.email}> and SENDER/SELLER {(seller.alternate_name).upper()} <{seller.customer.user.email}"
    log_transaction_activity(escrow_txn, description, request_meta)

    notify_seller_escrow_transaction_via_email(seller, buyer, merchant, escrow_txn)
    notify_merchant_escrow_transaction_via_email(seller, buyer, merchant, escrow_txn)

    return escrow_txn


def create_bulk_merchant_escrow_transactions(
    merchant: Merchant,
    buyer: User,
    entities: dict,
    source: Transaction,
    payout_config: PayoutConfig,
    currency: str,
    request_meta: dict,
):
    escrows = []
    for entity in entities:
        seller_email = entity["seller"]
        items = entity["items"]
        for item in items:
            txn = create_merchant_escrow_transaction(
                merchant,
                buyer.email,
                seller_email,
                item,
                source,
                payout_config,
                currency,
                request_meta,
            )
            escrows.append(txn)
    return escrows


def generate_deposit_transaction_for_escrow(
    user: User,
    amount: Decimal,
    tx_ref: str,
    meta: dict,
    currency: str,
    merchant: Merchant,
):
    meta.update({"title": "Escrow transaction fund"})
    deposit_txn = Transaction.objects.create(
        user_id=user,
        type="DEPOSIT",
        mode="MERCHANT_API",
        amount=amount,
        status="PENDING",
        reference=tx_ref,
        currency=currency,
        merchant=merchant,
        provider="FLUTTERWAVE",
        meta=meta,
    )

    return deposit_txn


def get_customer_merchant_instance(email, merchant) -> CustomerMerchant:
    instance = None
    try:
        user = User.objects.filter(email=email).first()
        instance = CustomerMerchant.objects.filter(
            merchant=merchant, customer=user.customer
        ).first()
    except Exception as e:
        print("Error getting customer merchant_instance", str(e))
    return instance


def get_merchant_escrow_users(escrow_txn: Transaction, merchant: Merchant):
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


def transactions_are_invalid_escrows(transactions):
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if not transaction:
            continue
        if transaction.type != "ESCROW":
            return True
    return False


def transactions_delivery_date_has_not_elapsed(transactions: list[str]) -> bool:
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if not transaction:
            continue
        delivery_date = transaction.escrowmeta.delivery_date
        if datetime.datetime.now().date() < delivery_date:
            return True
    return False


def transactions_are_already_unlocked(transactions):
    for id in transactions:
        transaction = get_transaction_by_id(id)
        if not transaction:
            continue
        if transaction.status == "SETTLED":
            return True
    return False


def settle_merchant_escrow_charges(
    transaction: Transaction,
    merchant: Merchant,
    request_meta: dict,
    merchant_payout_config: PayoutConfig,
) -> None:
    merchant_user_charges = get_merchant_transaction_charges(
        merchant, transaction.amount, merchant_payout_config
    )
    buyer_charge = merchant_user_charges.get("buyer_charge")
    seller_charge = merchant_user_charges.get("seller_charge")
    merchant_settlement = buyer_charge + seller_charge
    tx_ref = generate_txn_reference()
    currency = transaction.currency
    settlement_txn = Transaction.objects.create(
        user_id=merchant.user_id,
        type="MERCHANT_SETTLEMENT",
        merchant=merchant,
        amount=int(merchant_settlement),
        status="SUCCESSFUL",
        mode="MERCHANT_API",
        reference=tx_ref,
        currency=currency,
        provider="MYBALANCE",
        meta={
            "title": "Escrow Settlement",
            "description": "Merchant Escrow Settlement",
            "escrow_transaction": str(transaction.id),
        },
    )

    merchant_user = merchant.user_id

    description = f"Settlement with reference {tx_ref} generated to credit merchant wallet with {currency} {add_commas_to_transaction_amount(merchant_settlement)}"
    log_transaction_activity(transaction, description, request_meta)

    _, wallet = merchant_user.get_currency_wallet(currency)
    description = f"Previous Merchant Balance: {currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(transaction, description, request_meta)

    merchant_user.credit_wallet(merchant_settlement, currency)

    _, wallet = merchant_user.get_currency_wallet(currency)
    description = f"New Merchant Balance: {currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(transaction, description, request_meta)

    escrow_users = get_merchant_escrow_users(transaction, merchant)
    buyer = escrow_users.get("buyer")
    seller = escrow_users.get("seller")

    merchant_values = {
        "date": parse_datetime(transaction.updated_at),
        "amount_settled": f"{currency} {add_commas_to_transaction_amount(str(merchant_settlement))}",
        "transaction_amount": f"{currency} {add_commas_to_transaction_amount(str(transaction.amount))}",
        "buyer_charges": f"{currency} {add_commas_to_transaction_amount(str(buyer_charge))}",
        "seller_charges": f"{currency} {add_commas_to_transaction_amount(str(seller_charge))}",
        "transaction_id": (transaction.reference).upper(),
        "item_name": transaction.meta["title"],
        "delivery_date": parse_date(transaction.escrowmeta.delivery_date),
        "seller_name": seller.alternate_name,
        "seller_phone": seller.alternate_phone_number,
        "seller_email": seller.customer.user.email,
        "buyer_name": buyer.alternate_name,
        "buyer_phone": buyer.alternate_phone_number,
        "buyer_email": buyer.customer.user.email,
        "merchant_platform": transaction.merchant.name,
    }
    tasks.send_unlock_funds_merchant_email.delay(
        merchant.user_id.email, merchant_values
    )


def unlock_customer_escrow_transaction_by_id(id: UUID, user: User, request_meta: dict):
    try:
        txn = get_transaction_by_id(id)
        txn.status = "FUFILLED"
        txn.save()
        merchant = txn.merchant
        transaction_payout_config = (
            txn.escrowmeta.payout_config
            if txn.escrowmeta.payout_config
            else get_merchant_active_payout_configuration(merchant)
        )

        # Log Payout configuration used to settle transactions
        description = f"Payout Configuration used for settling funds: {(transaction_payout_config.name).upper()} <{str(transaction_payout_config)}>"
        log_transaction_activity(txn, description, request_meta)

        merchant_user_charges = get_merchant_transaction_charges(
            merchant, txn.amount, transaction_payout_config
        )
        merchant_seller_charge = merchant_user_charges.get("seller_charge")

        # Move amount from Buyer's Locked Balance to Unlocked Balance
        profile = user.userprofile
        user.update_locked_amount(
            amount=txn.amount,
            currency=txn.currency,
            mode="OUTWARD",
            type="DEBIT",
        )
        user.update_unlocked_amount(
            amount=txn.amount,
            currency=txn.currency,
            type="CREDIT",
        )

        # Evaluating seller free escrow transactions
        seller_charges = int(txn.charge) + int(merchant_seller_charge)
        amount_to_credit_seller = int(txn.amount - seller_charges)
        seller = User.objects.filter(email=txn.lockedamount.seller_email).first()
        escrow_credits_used = False
        if seller.userprofile.free_escrow_transactions > 0:
            # credit full amount to seller and deplete free credits
            amount_to_credit_seller = int(txn.amount) - int(merchant_seller_charge)
            seller_charges = int(merchant_seller_charge)
            seller.userprofile.free_escrow_transactions -= 1
            seller.userprofile.save()
            escrow_credits_used = True
        profile.save()
        locked_amount_instance = LockedAmount.objects.get(transaction=txn)

        # Credit amount to Seller's wallet balance after deducting applicable escrow fees
        seller.credit_wallet(amount_to_credit_seller, txn.currency)
        seller.update_locked_amount(
            amount=txn.amount,
            currency=txn.currency,
            mode="INWARD",
            type="DEBIT",
        )

        locked_amount_instance.status = "SETTLED"
        locked_amount_instance.save()

        escrow_credits_message = " " if escrow_credits_used else " not "
        description = (
            f"{txn.currency} {add_commas_to_transaction_amount(amount_to_credit_seller)} was released successfully by merchant: {(txn.merchant.name).upper()} <{txn.merchant.user_id.email}>. Escrow credit was"
            + escrow_credits_message
            + f"used to settle seller."
        )
        log_transaction_activity(txn, description, request_meta)

        seller_values = {
            "date": parse_datetime(txn.updated_at),
            "transaction_id": (txn.reference).upper(),
            "item_name": txn.meta["title"],
            "customer_name": user.name,
            "customer_email": user.email,
            "merchant_platform": (txn.merchant.name).upper(),
            "amount_unlocked": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
            "amount_settled": f"{txn.currency} {add_commas_to_transaction_amount(amount_to_credit_seller)}",
            "transaction_fee": f"{txn.currency} {add_commas_to_transaction_amount(seller_charges)}",
        }
        buyer_values = {
            "date": parse_datetime(txn.updated_at),
            "transaction_id": (txn.reference).upper(),
            "item_name": txn.meta["title"],
            "seller_name": seller.name,
            "seller_email": seller.email,
            "merchant_platform": (txn.merchant.name).upper(),
            "amount_unlocked": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
        }

        tasks.send_unlock_funds_merchant_seller_email.delay(seller.email, seller_values)
        tasks.send_unlock_funds_merchant_buyer_email.delay(user.email, buyer_values)

        # Create Notification for Buyer
        UserNotification.objects.create(
            user=user,
            category="FUNDS_UNLOCKED_BUYER",
            title=notifications.FundsUnlockedBuyerNotification(
                add_commas_to_transaction_amount(txn.amount), txn.currency
            ).TITLE,
            content=notifications.FundsUnlockedBuyerNotification(
                add_commas_to_transaction_amount(txn.amount), txn.currency
            ).CONTENT,
            action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{txn.reference}",
        )

        # Create Notification for Seller
        UserNotification.objects.create(
            user=seller,
            category="FUNDS_UNLOCKED_SELLER",
            title=notifications.FundsUnlockedSellerNotification(
                add_commas_to_transaction_amount(txn.amount), txn.currency
            ).TITLE,
            content=notifications.FundsUnlockedSellerNotification(
                add_commas_to_transaction_amount(txn.amount), txn.currency
            ).CONTENT,
            action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{txn.reference}",
        )
        # Settle Merchant Funds
        settle_merchant_escrow_charges(
            txn, merchant, request_meta, transaction_payout_config
        )
        return True, "Funds unlocked successfully."
    except Exception as e:
        print(
            f"Exception occurred while unlocking funds with transaction {id}: {str(e)}"
        )
        return (
            False,
            "An error occurred while unlocking funds with transaction. Kindly contact Support",
        )


def unlock_customer_escrow_transactions(
    transactions: list, user: User, request_meta: dict
):
    for transaction in transactions:
        id = str(transaction)
        err = False
        try:
            unlock_customer_escrow_transaction_by_id(id, user, request_meta)
        except Exception as e:
            print(
                f"Exception occurred while unlocking funds with transaction {id}: {str(e)}"
            )
            err = True

    if err:
        return (
            False,
            "An error occurred while unlocking funds with one or more transactions. Contact Support.",
        )
    else:
        return True, "Funds unlocked successfully."


def create_bulk_merchant_transactions_and_products_and_log_activity(
    txn: Transaction, user: User, request_meta: dict
) -> list[str]:
    escrow_entities = txn.meta.get("seller_escrow_breakdown")
    payout_config_id = txn.meta.get("payout_config")
    payout_config = PayoutConfig.objects.filter(id=payout_config_id).first()
    merchant_id = txn.meta.get("merchant")
    merchant = get_merchant_by_id(merchant_id)

    # create bulk escrow transactions from entities data
    escrows = create_bulk_merchant_escrow_transactions(
        merchant,
        user,
        escrow_entities,
        txn,
        payout_config,
        txn.currency,
        request_meta,
    )
    products = []
    escrow_references = []
    for transaction in escrows:
        escrow_users = get_merchant_escrow_users(transaction, merchant)
        seller: CustomerMerchant = escrow_users.get("seller")
        products.append(
            {
                "name": transaction.escrowmeta.item_type,
                "quantity": transaction.escrowmeta.item_quantity,
                "amount": f"{txn.currency} {add_commas_to_transaction_amount(transaction.amount)}",
                "store_owner": seller.alternate_name,
            }
        )
        escrow_references.append(transaction.reference)

    formatted_escrow_references = f"[{', '.join(escrow_references)}]"
    description = (
        f"Escrow transaction(s) {formatted_escrow_references} successfully created"
    )
    log_transaction_activity(txn, description, request_meta)

    return products, escrow_references


def generate_api_key(merchant_id):
    api_key = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        merchant_id.encode("utf-8") + time.ctime().encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    hashed_api_key = bcrypt.hashpw(api_key.encode("utf-8"), bcrypt.gensalt())
    return api_key, hashed_api_key.decode("utf-8")


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    return bcrypt.checkpw(api_key.encode("utf-8"), hashed_api_key.encode("utf-8"))
