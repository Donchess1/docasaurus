import uuid
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class BankAccount(models.Model):
    id = models.UUIDField(unique=True, primary_key=True,
                          default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id
