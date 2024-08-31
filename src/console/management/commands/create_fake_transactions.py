import random
from datetime import datetime

from django.core.management.base import BaseCommand
from faker import Faker

from console.models import Transaction
from merchant.models import Merchant
from users.models import CustomUser


class Command(BaseCommand):
    help = "Generate fake transaction data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10000,
            help="The number of fake transactions to create (default is 10,000)",
        )

    def handle(self, *args, **kwargs):
        count = kwargs["count"]
        fake = Faker()

        # Define choices from your model
        status_choices = [status[0] for status in Transaction.STATUS]
        type_choices = [t_type[0] for t_type in Transaction.TYPES]
        currency_choices = [currency[0] for currency in Transaction.CURRENCY]
        provider_choices = [provider[0] for provider in Transaction.PROVIDER]

        # Function to generate a single fake transaction
        def create_fake_transaction():
            return Transaction(
                user_id=CustomUser.objects.order_by("?").first(),  # Random user
                status=random.choice(status_choices),
                type=random.choice(type_choices),
                mode=fake.random_element(elements=("WEB", "MERCHANT_API")),
                reference=fake.uuid4(),
                narration=fake.sentence(),
                amount=random.randint(
                    100, 1000000
                ),  # Random amount between 100 and 1,000,000
                charge=random.randint(10, 10000),  # Random charge between 10 and 10,000
                remitted_amount=random.randint(90, 990000),  # Random remitted amount
                currency=random.choice(currency_choices),
                provider=random.choice(provider_choices),
                provider_tx_reference=fake.uuid4(),
                meta={"description": fake.text()},
                verified=fake.boolean(
                    chance_of_getting_true=80
                ),  # 80% chance of being true
                merchant=Merchant.objects.order_by("?").first(),  # Random merchant
                created_at=fake.date_time_between(
                    start_date="-1y", end_date="now"
                ),  # Random date within the last year
                updated_at=datetime.now(),
            )

        # Generate and save the fake transactions
        transactions = [create_fake_transaction() for _ in range(count)]
        Transaction.objects.bulk_create(transactions)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {count} fake transactions.")
        )
