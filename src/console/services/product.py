from django.contrib.auth import get_user_model
from django.db import transaction

from console.models import Product, Transaction

User = get_user_model()


@transaction.atomic
def create_product_purchase_transaction(
    product: Product, tx_ref: str, user: User, charges: int, quantity: int
):
    txn = Transaction.objects.create(
        user_id=user,
        charge=charges,
        type="PRODUCT",
        mode="WEB",
        amount=product.price * quantity,
        status="PENDING",
        reference=tx_ref,
        currency=product.currency,
        provider="MYBALANCE",
        provider_tx_reference=tx_ref,
        product=product,
        meta={
            "title": f"{product.name}",
            "description": f"Event Name: {product.event.name}. Ticket Tier:{product.name}",
            "ticket_quantity": quantity,
        },
    )
    return txn
