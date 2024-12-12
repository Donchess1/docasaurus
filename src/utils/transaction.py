from django.contrib.auth import get_user_model
from django.db import transaction

from console.models.transaction import Transaction
from merchant.utils import (
    get_merchant_escrow_users,
    unlock_customer_escrow_transaction_by_id,
)

User = get_user_model()


def get_transaction_instance(ref_or_id):
    try:
        instance = Transaction.objects.filter(reference=ref_or_id).first()
        if instance is None:
            instance = Transaction.objects.filter(id=ref_or_id).first()
    except Exception as e:
        instance = None
    return instance


def get_escrow_transaction_stakeholders(transaction: Transaction):
    try:
        escrow_meta = transaction.escrowmeta
        author = escrow_meta.author
        if author == "BUYER":
            buyer_email = transaction.user_id.email
            seller_email = escrow_meta.partner_email
        elif author == "SELLER":
            seller_email = transaction.user_id.email
            buyer_email = escrow_meta.partner_email
        elif author == "MERCHANT":
            parties = escrow_meta.meta.get("parties", {})
            buyer_email = parties.get("buyer")
            seller_email = parties.get("seller")
        else:
            buyer_email = None
            seller_email = None

        return {"BUYER": buyer_email, "SELLER": seller_email}
    except Exception as e:
        print("Error Fetching Escrow Transaction  Stakeholders: ", str(e))
        return {}


def invert_escrow_transaction_stakeholders(stakeholders):
    if not stakeholders.get("BUYER") or not stakeholders.get("SELLER"):
        return stakeholders  # Return as-is if either email is missing

    buyer_email = stakeholders["BUYER"]
    seller_email = stakeholders["SELLER"]

    # Add inverted mappings
    stakeholders[buyer_email] = "BUYER"
    stakeholders[seller_email] = "SELLER"
    return stakeholders


def get_escrow_transaction_users(transaction: Transaction) -> dict:
    # transaction.mode == ["WEB", "MERCHANT_API"]
    if (transaction.mode).upper() == "WEB":
        partner_email = transaction.escrowmeta.partner_email
        if transaction.escrowmeta.author == "BUYER":
            buyer = transaction.user_id
            seller = User.objects.filter(email=partner_email).first()
            return {
                "BUYER": {"name": buyer.name, "email": buyer.email},
                "SELLER": {
                    "name": seller.name if seller else partner_email,
                    "email": seller.email if seller else partner_email,
                },
                "MERCHANT": {"name": "MyBalance", "email": "mybalance@oinvent.com"},
            }
        else:
            seller = transaction.user_id
            buyer = User.objects.filter(email=partner_email).first()
            return {
                "BUYER": {
                    "name": buyer.name if buyer else partner_email,
                    "email": buyer.email if buyer else partner_email,
                },
                "SELLER": {"name": seller.name, "email": seller.email},
                "MERCHANT": {"name": "MyBalance", "email": "mybalance@oinvent.com"},
            }
    else:
        parties = get_merchant_escrow_users(transaction, transaction.merchant)
        buyer = parties.get("buyer")
        seller = parties.get("seller")
        return {
            "BUYER": {"name": buyer.alternate_name, "email": buyer.customer.user.email},
            "SELLER": {
                "name": seller.alternate_name,
                "email": seller.customer.user.email,
            },
            "MERCHANT": {
                "name": transaction.merchant.user_id.name,
                "email": transaction.merchant.user_id.email,
            },
        }


def get_merchant_escrow_transaction_stakeholders(id):
    buyer_email, seller_email, merchant_email = None, None, None
    try:
        transaction = get_transaction_instance(id)
        if transaction.escrowmeta.meta:
            meta = transaction.escrowmeta.meta
            parties = meta.get("parties")
            buyer_email = parties.get("buyer")
            seller_email = parties.get("seller")
            merchant_email = transaction.merchant.user_id.email
    except Exception as e:
        print("Error Fetching Merchant Escrow Transaction  Stakeholders: ", str(e))

    return {"BUYER": buyer_email, "SELLER": seller_email, "MERCHANT": merchant_email}


@transaction.atomic
def release_escrow_funds_by_merchant(
    transaction: Transaction, request_meta: dict
) -> bool:
    stakeholders = get_merchant_escrow_transaction_stakeholders(str(transaction))
    user = User.objects.filter(email=stakeholders["BUYER"]).first()
    completed, message = unlock_customer_escrow_transaction_by_id(
        transaction.id, user, request_meta
    )
    return completed, message
