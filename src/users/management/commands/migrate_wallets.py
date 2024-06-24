from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import CustomUser, Wallet


class Command(BaseCommand):
    help = "Migrate wallet data from UserProfile to Wallet model"

    def handle(self, *args, **kwargs):
        users = CustomUser.objects.all()
        created_wallets = 0
        updated_wallets = 0

        with transaction.atomic():
            for user in users:
                try:
                    profile = user.userprofile
                    wallet, created = Wallet.objects.get_or_create(
                        user=user, currency="NGN"
                    )

                    wallet.balance = profile.wallet_balance
                    wallet.unlocked_amount = profile.unlocked_amount
                    wallet.withdrawn_amount = profile.withdrawn_amount

                    if user.is_buyer:
                        wallet.locked_amount_outward = profile.locked_amount
                    elif user.is_seller:
                        wallet.locked_amount_inward = profile.locked_amount

                    wallet.save()

                    if created:
                        created_wallets += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Created NGN wallet for user {user.email}"
                            )
                        )
                    else:
                        updated_wallets += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated NGN wallet for user {user.email}"
                            )
                        )

                except CustomUser.userprofile.RelatedObjectDoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"UserProfile does not exist for user {user.email}"
                        )
                    )
                except ValidationError as e:
                    self.stdout.write(
                        self.style.ERROR(f"Validation error for user {user.email}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_wallets} wallets and updated {updated_wallets} wallets."
            )
        )
