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
