import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models.user import CustomUser


class UserNotification(models.Model):
    NOTIFICATION_CATEGORIES = (
        ("DEPOSIT", "DEPOSIT"),
        ("PRODUCT_PURCHASE_SUCCESSFUL", "PRODUCT_PURCHASE_SUCCESSFUL"),
        ("WITHDRAWAL", "WITHDRAWAL"),
        ("ESCROW_APPROVED", "ESCROW_APPROVED"),
        ("ESCROW_REJECTED", "ESCROW_REJECTED"),
        ("FUNDS_LOCKED_BUYER", "FUNDS_LOCKED_BUYER"),
        ("FUNDS_LOCKED_SELLER", "FUNDS_LOCKED_SELLER"),
        ("FUNDS_UNLOCKED_BUYER", "FUNDS_UNLOCKED_BUYER"),
        ("FUNDS_UNLOCKED_SELLER", "FUNDS_UNLOCKED_SELLER"),
        ("DISPUTE_RAISED_AUTHOR", "DISPUTE_RAISED_AUTHOR"),
        ("DISPUTE_RAISED_RECIPIENT", "DISPUTE_RAISED_RECIPIENT"),
        ("DISPUTE_RESOLVED", "DISPUTE_RESOLVED"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.CharField(max_length=255, choices=NOTIFICATION_CATEGORIES)
    title = models.CharField(max_length=255, null=True)
    content = models.TextField()
    is_seen = models.BooleanField(default=False)
    action_url = models.URLField(
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("is_seen", "-created_at")

    def __str__(self):
        return f"{self.user}-{self.category}"
