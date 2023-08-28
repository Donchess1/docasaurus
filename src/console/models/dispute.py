import uuid

from django.db import models

from console.models.transaction import Transaction
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
    priority = models.CharField(max_length=255, choices=PRIORITY)
    reason = models.CharField(max_length=255)
    description = models.TextField()
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispute - Transaction ID: {self.transaction}"
