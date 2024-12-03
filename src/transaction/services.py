from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from utils.transaction import get_escrow_transaction_users

User = get_user_model()


def get_escrow_transaction_parties_info(transaction: Transaction) -> dict:
    users = get_escrow_transaction_users(transaction)
    buyer = users.get("BUYER")
    seller = users.get("SELLER")
    merchant = users.get("MERCHANT")
    parties = {
        "buyer": {
            "name": buyer["name"] if buyer else "",
            "email": buyer["email"] if buyer else "",
        },
        "seller": {
            "name": seller["name"] if seller else "",
            "email": seller["email"] if seller else "",
        },
        "merchant": {
            "name": merchant["name"] if merchant else "",
            "email": merchant["email"] if merchant else "",
        },
    }
    return parties


def get_user_owned_transaction_queryset(
    user: User, currency: str = "NGN"
) -> QuerySet[Transaction]:
    # Transactions where user is the main user or user is involved in escrow
    # this includes all deposits, withdrawals and escrow transactions --> DEPOSIT, WITHDRAW, ESCROW
    # product purchases and settlement transactions --> PRODUCT, SETTLEMENT
    # merchant API settlement transactions --> MERCHANT_SETTLEMENT
    # where the user was a stakeholder
    queryset = (
        Transaction.objects.filter(
            (
                Q(user_id=user)
                | Q(escrowmeta__partner_email=user.email)
                | Q(escrowmeta__meta__parties__buyer=user.email)
                | Q(escrowmeta__meta__parties__seller=user.email)
            )
            & Q(currency=currency)
        )
        .order_by("-created_at")
        .distinct()
    )
    return queryset
