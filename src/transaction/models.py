import uuid

from django.db import models

from console.models.transaction import Transaction


class TransactionActivityLog(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, db_index=True
    )
    description = models.TextField()
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"
