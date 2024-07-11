import uuid
from decimal import Decimal, InvalidOperation

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction

from users.models.wallet import Wallet
from utils.utils import CURRENCIES


class Manager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=50, unique=True)
    is_verified = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_merchant = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = Manager()

    def __str__(self):
        return self.email

    def create_wallet(self):
        for currency in CURRENCIES:  # Consider creating wallets after KYC
            wallet, created = Wallet.objects.get_or_create(
                user=self,
                currency=currency,
            )

    def validate_amount_and_currency(self, amount, currency):
        if currency not in CURRENCIES:
            raise ValidationError("Invalid currency.")
        try:
            amount = Decimal(str(amount))  # Ensure amount is Decimal-compatible
        except InvalidOperation:
            raise ValidationError("Invalid amount value.")

        if amount < 0:
            raise ValidationError("Amount must be greater than 0")

    def get_wallets(self):
        wallets = Wallet.objects.filter(user=self)
        if not wallets:
            return False, f"User has no wallets."
        return True, wallets

    def get_currency_wallet(self, currency):
        if currency not in CURRENCIES:
            return False, "Invalid currency."

        wallet = Wallet.objects.filter(user=self, currency=currency).first()
        if not wallet:
            return False, f"{currency.upper()} wallet for user does not exist."

        return True, wallet

    def validate_wallet_withdrawal_amount(self, amount, currency):
        if currency not in CURRENCIES:
            return False, "Invalid currency."
        try:
            amount = Decimal(str(amount))  # Ensure amount is Decimal-compatible
        except InvalidOperation:
            return False, "Invalid amount value."

        if amount <= 0:
            return False, "Amount must be greater than 0"

        wallet = Wallet.objects.filter(user=self, currency=currency).first()
        if not wallet:
            return False, f"{currency.upper()} wallet for user does not exist."

        if wallet.balance < amount:
            return False, "Insufficient funds."

        return True, None

    def credit_wallet(self, amount, currency="NGN"):
        self.validate_amount_and_currency(amount, currency)

        with transaction.atomic():
            wallet = Wallet.objects.filter(user=self, currency=currency).first()
            if not wallet:
                raise ValidationError(
                    f"{currency.upper()} wallet for user does not exist."
                )
            wallet.balance += Decimal(str(amount))
            wallet.save()

    def debit_wallet(self, amount, currency="NGN"):
        self.validate_amount_and_currency(amount, currency)

        with transaction.atomic():
            wallet = Wallet.objects.filter(user=self, currency=currency).first()
            if not wallet:
                raise ValidationError(
                    f"{currency.upper()} wallet for user does not exist."
                )
            if wallet.balance < amount:
                raise ValidationError("Insufficient funds.")
            wallet.balance -= Decimal(str(amount))
            wallet.save()

    def update_locked_amount(self, amount, currency="NGN", mode=None, type=None):
        self.validate_amount_and_currency(amount, currency)

        if mode not in ["INWARD", "OUTWARD"]:
            raise ValidationError("Invalid mode. Must be 'INWARD' or 'OUTWARD'.")

        if type not in ["CREDIT", "DEBIT"]:
            raise ValidationError("Invalid type. Must be 'CREDIT' or 'DEBIT'.")

        with transaction.atomic():
            wallet = Wallet.objects.filter(user=self, currency=currency).first()
            if not wallet:
                raise ValidationError(
                    f"{currency.upper()} wallet for user does not exist."
                )

            if mode == "INWARD":
                if type == "CREDIT":
                    wallet.locked_amount_inward += Decimal(str(amount))
                elif type == "DEBIT":
                    wallet.locked_amount_inward -= Decimal(str(amount))
            elif mode == "OUTWARD":
                if type == "CREDIT":
                    wallet.locked_amount_outward += Decimal(str(amount))
                elif type == "DEBIT":
                    wallet.locked_amount_outward -= Decimal(str(amount))
            wallet.save()

    def update_unlocked_amount(self, amount, currency="NGN", type=None):
        self.validate_amount_and_currency(amount, currency)

        if type not in ["CREDIT", "DEBIT"]:
            raise ValidationError("Invalid type. Must be 'CREDIT' or 'DEBIT'.")

        with transaction.atomic():
            wallet = Wallet.objects.filter(user=self, currency=currency).first()
            if not wallet:
                raise ValidationError(
                    f"{currency.upper()} wallet for user does not exist."
                )

            if type == "CREDIT":
                wallet.unlocked_amount += Decimal(str(amount))
            elif type == "DEBIT":
                wallet.unlocked_amount -= Decimal(str(amount))

            wallet.save()

    def update_withdrawn_amount(self, amount, currency="NGN"):
        self.validate_amount_and_currency(amount, currency)

        with transaction.atomic():
            wallet = Wallet.objects.filter(user=self, currency=currency).first()
            if not wallet:
                raise ValidationError(
                    f"{currency.upper()} wallet for user does not exist."
                )

            wallet.withdrawn_amount += Decimal(str(amount))
            wallet.save()
