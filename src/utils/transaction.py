from django.contrib.auth import get_user_model
from django.db import transaction

from console.models.transaction import Transaction
from merchant.utils import (
    get_merchant_escrow_users,
    unlock_customer_escrow_transaction_by_id,
)

User = get_user_model()


def get_escrow_transaction_stakeholders(tx_ref):
    try:
        transaction = Transaction.objects.get(reference=tx_ref)

        if transaction.escrowmeta.author == "BUYER":
            buyer_email = transaction.user_id.email
            seller_email = transaction.escrowmeta.partner_email
        else:
            seller_email = transaction.user_id.email
            buyer_email = transaction.escrowmeta.partner_email

        return {"BUYER": buyer_email, "SELLER": seller_email}

    except Transaction.DoesNotExist:
        return {}


def get_escrow_transaction_users(transaction: Transaction) -> dict:
    # transaction.mode == ["Web", "MERCHANT_API"]
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
        transaction = Transaction.objects.get(id=id)
        if transaction.escrowmeta.meta:
            meta = transaction.escrowmeta.meta
            parties = meta.get("parties")
            buyer_email = parties.get("buyer")
            seller_email = parties.get("seller")
            merchant_email = (transaction.merchant.user_id.email,)
    except Exception as e:
        print("Error Fetching Merchant Escrow Transactio  Stakeholders: ", str(e))

    return {"BUYER": buyer_email, "SELLER": seller_email, "MERCHANT": merchant_email}


@transaction.atomic
def release_escrow_funds_by_merchant(transaction):
    stakeholders = get_merchant_escrow_transaction_stakeholders(str(transaction))
    user = User.objects.filter(email=stakeholders["BUYER"]).first()
    completed = unlock_customer_escrow_transaction_by_id(transaction.id, user)
    if not completed:
        raise serializers.ValidationError(
            {"error": "Transaction could not be unlocked"}
        )
    return completed
