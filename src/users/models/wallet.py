import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Wallet(models.Model):
    CURRENCY_CHOICES = [
        ("NGN", "Nigerian Naira"),
        ("USD", "US Dollar"),
    ]
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    locked_amount_outward = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    locked_amount_inward = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    unlocked_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    withdrawn_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "currency")

    def clean(self):
        if (
            Wallet.objects.filter(user=self.user, currency=self.currency)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(f"{self.currency.upper()} wallet already exists!")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.currency}: {self.balance}"

    def get_queryset(self, currency):
        return self.__class__.objects.filter(id=self.id, currency=currency)

    @transaction.atomic()
    def credit(self, amount, currency):
        obj = self.get_queryset(currency=currency).select_for_update().get()
        obj.balance += Decimal(str(amount))
        obj.save()

    @transaction.atomic()
    def debit(self, amount, currency):
        obj = self.get_queryset(currency=currency).select_for_update().get()
        if amount > obj.balance:
            # raise errors.InsufficientFunds()
            # TODO: flag wallet
            pass
        obj.balance -= Decimal(str(amount))
        obj.save()
