from django.contrib.auth import get_user_model
from django.db import transaction

from console.models import Product, Transaction

User = get_user_model()


@transaction.atomic
def create_product_purchase_transaction(
    product: Product, tx_ref: str, user: User, charges: int
):
    txn = Transaction.objects.create(
        user_id=user,
        charge=charges,
        type="PRODUCT",
        mode="WEB",
        amount=product.price,
        status="PENDING",
        reference=tx_ref,
        currency=product.currency,
        provider="MYBALANCE",
        provider_tx_reference=tx_ref,
        product=product,
    )
    return txn
