import uuid

from django.db import models

from merchant.models import Merchant, PayoutConfig
from users.models.user import CustomUser

from .product import Product


class Transaction(models.Model):
    STATUS = (
        ("PENDING", "PENDING"),
        ("SUCCESSFUL", "SUCCESSFUL"),
        ("FAILED", "FAILED"),
        ("CANCELLED", "CANCELLED"),
        ("PAUSED", "PAUSED"),
        ("FUFILLED", "FUFILLED"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
        ("REVOKED", "REVOKED"),
        ("EXPIRED", "EXPIRED"),
    )
    TYPES = (
        ("DEPOSIT", "DEPOSIT"),
        ("WITHDRAW", "WITHDRAW"),
        ("ESCROW", "ESCROW"),
        ("MERCHANT_SETTLEMENT", "MERCHANT_SETTLEMENT"),
        ("PRODUCT", "PRODUCT"),
        (
            "SETTLEMENT",
            "SETTLEMENT",
        ),  # Product purchases are eventually resolved as settlements into product owner's wallet
    )
    PROVIDER = (
        ("FLUTTERWAVE", "FLUTTERWAVE"),
        ("PAYSTACK", "PAYSTACK"),
        ("BLUSALT", "BLUSALT"),
        ("TERRASWITCH", "TERRASWITCH"),
        ("STRIPE", "STRIPE"),
        ("MYBALANCE", "MYBALANCE"),
    )
    CURRENCY = (
        ("NGN", "NGN"),
        ("USD", "USD"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=STATUS, db_index=True)
    type = models.CharField(max_length=255, choices=TYPES, db_index=True)
    mode = models.CharField(max_length=255)
    provider_mode = models.CharField(max_length=255, null=True, blank=True)
    reference = models.CharField(max_length=255, unique=True)
    narration = models.CharField(max_length=255, null=True, blank=True)
    amount = models.IntegerField(default=0, null=True, blank=True)
    charge = models.IntegerField(default=0, null=True, blank=True)
    remitted_amount = models.IntegerField(default=0, null=True, blank=True)
    currency = models.CharField(
        max_length=255, default="NGN", choices=CURRENCY, db_index=True
    )
    provider = models.CharField(max_length=255, choices=PROVIDER, db_index=True)
    provider_tx_reference = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    merchant = models.ForeignKey(
        Merchant, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"


class EscrowMeta(models.Model):
    AUTHOR = (
        ("BUYER", "BUYER"),
        ("SELLER", "SELLER"),
        ("MERCHANT", "MERCHANT"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    author = models.CharField(max_length=255, choices=AUTHOR)
    transaction_id = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    partner_email = models.EmailField()
    purpose = models.TextField()
    item_type = models.CharField(max_length=255)
    item_quantity = models.IntegerField()
    delivery_date = models.DateField()
    delivery_tolerance = models.IntegerField(null=True, blank=True, default=3)
    charge = models.IntegerField(null=True, blank=True)
    payout_config = models.ForeignKey(
        PayoutConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    parent_payment_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_payment_transaction",
    )
    buyer_consent_to_unlock = models.BooleanField(default=False)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"


class LockedAmount(models.Model):
    STATUS_CHOICES = (
        ("ESCROW", "ESCROW"),
        ("SETTLED", "SETTLED"),
        ("DISPUTE_RAISED", "DISPUTE_RAISED"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="locked_amounts"
    )
    seller_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"LockedAmount - Transaction ID: {self.transaction_id}"
