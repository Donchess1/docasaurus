import uuid

from django.db import models

from users.models.user import CustomUser


class Transaction(models.Model):
    STATUS = (
        ("PENDING", "PENDING"),
        ("SUCCESSFUL", "SUCCESSFUL"),
        ("FAILED", "FAILED"),
        ("CANCELLED", "CANCELLED"),
    )
    TYPES = (
        ("DEPOSIT", "DEPOSIT"),
        ("WITHDRAW", "WITHDRAW"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=STATUS)
    type = models.CharField(max_length=255, choices=TYPES)
    mode = models.CharField(max_length=255)
    reference = models.CharField(max_length=255)
    narration = models.CharField(max_length=255, null=True, blank=True)
    amount = models.IntegerField(default=0, null=True, blank=True)
    charge = models.IntegerField(default=0, null=True, blank=True)
    remitted_amount = models.IntegerField(default=0, null=True, blank=True)
    currency = models.CharField(max_length=255, default="NGN")
    provider = models.CharField(max_length=255)
    provider_tx_reference = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"


# class EscrowTransaction(models.Model):
#     STATUS = (
#         ("PENDING", "PENDING"),
#         ("PROGRESS", "PROGRESS"),
#         ("SUCCESSFUL", "SUCCESSFUL"),
#         ("FAILED", "FAILED"),
#     )
#     id = models.UUIDField(
#         unique=True, primary_key=True, default=uuid.uuid4, editable=False
#     )
#     buyer_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     seller_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     status = models.CharField(max_length=255, choices=STATUS)
#     purpose = models.TextField()
#     type_of_items = models.CharField(max_length=255)
#     number_of_items = models.IntegerField()
#     amount = models.IntegerField()
#     delivery_date = models.DateTimeField()
#     delivery_tolerance = models.IntegerField(null=True, blank=True, default=3)
#     charge = models.IntegerField(null=True, blank=True)
#     meta = models.JSONField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.id}"
