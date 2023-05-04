import uuid

from django.db import models

from business.models.business import Business
from users.models.user import CustomUser

from .kyc import UserKYC


class UserProfile(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = user_id = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    kyc_id = models.ForeignKey(
        UserKYC, on_delete=models.SET_NULL, null=True, blank=True
    )
    business_id = models.ForeignKey(
        Business, on_delete=models.SET_NULL, null=True, blank=True
    )
    avatar = models.URLField(null=True, blank=True)
    profile_link = models.URLField(null=True, blank=True)
    wallet_balance = models.IntegerField(default=0, null=True, blank=True)
    locked_amount = models.IntegerField(default=0, null=True, blank=True)
    unlocked_amount = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"
