from console.models.transaction import Transaction


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
        return None


def get_merchant_escrow_transaction_stakeholders(id):
    buyer, seller, merchant = None, None, None
    try:
        transaction = Transaction.objects.get(id=id)
        if transaction.escrowmeta:
            if transaction.escrowmeta.meta:
                meta = transaction.escrowmeta.meta
                parties = meta.get("parties")
                buyer_email = parties.get("buyer")
                seller_email = parties.get("seller")
                merchant = transaction.merchant
    except Exception as e:
        print(str(e))
        {"BUYER": buyer, "SELLER": seller, "MERCHANT": merchant}

    return {
        "BUYER": buyer_email,
        "SELLER": seller_email,
        "MERCHANT": merchant.user_id.email,
    }
