from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import CustomUser, Wallet


class Command(BaseCommand):
    help = "Create wallet instances for all users in USD and NGN"

    def handle(self, *args, **kwargs):
        users = CustomUser.objects.all()
        currencies = ["USD", "NGN"]
        created_wallets = 0
        existing_wallets = 0

        with transaction.atomic():
            for user in users:
                for currency in currencies:
                    wallet, created = Wallet.objects.get_or_create(
                        user=user, currency=currency
                    )
                    if created:
                        created_wallets += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Created {currency} wallet for user {user.email}"
                            )
                        )
                    else:
                        existing_wallets += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"{currency} wallet already exists for user {user.email}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_wallets} wallets. {existing_wallets} wallets already existed."
            )
        )
