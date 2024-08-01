from console.models.transaction import EscrowMeta, LockedAmount, Transaction
from utils.transaction import get_escrow_transaction_users


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
