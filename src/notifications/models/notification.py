import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models.user import CustomUser


class UserNotification(models.Model):
    NOTIFICATION_CATEGORIES = (
        ("DEPOSIT", "DEPOSIT"),
        ("WITHDRAWAL", "WITHDRAWAL"),
        ("FUNDS_LOCKED_BUYER", "FUNDS_LOCKED_BUYER"),
        ("FUDNS_LOCKED_SELLER", "FUDNS_LOCKED_SELLER"),
        ("FUNDS_UNLOCKED_BUYER", "FUNDS_UNLOCKED_BUYER"),
        ("FUDNS_UNLOCKED_SELLER", "FUDNS_UNLOCKED_SELLER"),
        ("DISPUTE_RAISED_AUTHOR", "DISPUTE_RAISED_AUTHOR"),
        ("DISPUTE_RAISED_RECIPIENT", "DISPUTE_RAISED_RECIPIENT"),
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
        return f"{self.category}"
