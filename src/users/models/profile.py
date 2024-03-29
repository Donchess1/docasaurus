import uuid

from django.db import models
from django.utils import timezone

from business.models.business import Business
from notifications.models.notification import UserNotification
from users.models.user import CustomUser

from .bank_account import BankAccount
from .kyc import UserKYC


class UserProfile(models.Model):
    USER_TYPES = (
        ("BUYER", "BUYER"),
        ("SELLER", "SELLER"),
        ("CONTRACTOR", "CONTRACTOR"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = user_id = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=255, choices=USER_TYPES)
    kyc_id = models.ForeignKey(
        UserKYC, on_delete=models.SET_NULL, null=True, blank=True
    )
    business_id = models.ForeignKey(
        Business, on_delete=models.SET_NULL, null=True, blank=True
    )
    bank_account_id = models.ForeignKey(
        BankAccount, on_delete=models.SET_NULL, null=True, blank=True
    )
    avatar = models.URLField(null=True, blank=True)
    profile_link = models.URLField(null=True, blank=True)
    wallet_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    show_tour_guide = models.BooleanField(default=True)
    phone_number_flagged = models.BooleanField(default=False)
    locked_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    free_escrow_transactions = models.IntegerField(default=5)
    unlocked_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    withdrawn_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id.email}"

    def notification_count(self):
        return UserNotification.objects.filter(user=self.user_id, is_seen=False).count()
