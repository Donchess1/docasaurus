import uuid

from django.contrib.auth import get_user_model
from django.db import models, transaction

from merchant.models import Merchant
from users.models import CustomUser


class BankAccount(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_code = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=10, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"


@transaction.atomic
def set_most_recent_bank_account_as_default():
    # Get all bank accounts, ordered by user_id and created_at (or updated_at)
    bank_accounts = BankAccount.objects.all().order_by("user_id", "-created_at")

    # Keep track of the previous user_id
    prev_user_id = None
    for bank_account in bank_accounts:
        if bank_account.user_id != prev_user_id:
            # New user, set the most recent bank account to default (this is the first instance for this user)
            bank_account.is_default = True
        else:
            # Not the most recent for this user, set is_default to False
            bank_account.is_default = False

        bank_account.save()

        # Update prev_user_id to the current one
        prev_user_id = bank_account.user_id
