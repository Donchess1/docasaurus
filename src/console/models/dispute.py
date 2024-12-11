import uuid

from django.db import models

from console.models.transaction import Transaction
from merchant.models import Merchant
from users.models.user import CustomUser


class Dispute(models.Model):
    STATUS = (
        ("PENDING", "PENDING"),
        ("RESOLVED", "RESOLVED"),
        ("REJECTED", "REJECTED"),
        ("PROGRESS", "PROGRESS"),
    )
    PRIORITY = (
        ("HIGH", "HIGH"),
        ("MEDIUM", "MEDIUM"),
        ("LOW", "LOW"),
    )
    AUTHOR = (
        ("BUYER", "BUYER"),
        ("SELLER", "SELLER"),
    )
    SOURCE = (
        ("PLATFORM", "PLATFORM"),
        ("API", "API"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    author = models.CharField(max_length=255, choices=AUTHOR)
    buyer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="buyer_user"
    )
    seller = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="seller_user"
    )
    status = models.CharField(max_length=255, choices=STATUS)
    source = models.CharField(max_length=255, choices=SOURCE, default="PLATFORM")
    priority = models.CharField(max_length=255, choices=PRIORITY)
    reason = models.CharField(max_length=255)
    merchant = models.ForeignKey(
        Merchant, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    description = models.TextField()
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispute - Transaction ID: {self.transaction}"

    def save(self, *args, **kwargs):
        if self.transaction and not self.merchant:
            self.merchant = self.transaction.merchant
        super().save(*args, **kwargs)
