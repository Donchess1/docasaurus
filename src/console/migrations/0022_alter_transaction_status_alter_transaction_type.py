# Generated by Django 4.1.2 on 2024-06-23 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("console", "0021_alter_transaction_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "PENDING"),
                    ("SUCCESSFUL", "SUCCESSFUL"),
                    ("FAILED", "FAILED"),
                    ("CANCELLED", "CANCELLED"),
                    ("PAUSED", "PAUSED"),
                    ("FUFILLED", "FUFILLED"),
                    ("APPROVED", "APPROVED"),
                    ("REJECTED", "REJECTED"),
                ],
                db_index=True,
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="type",
            field=models.CharField(
                choices=[
                    ("DEPOSIT", "DEPOSIT"),
                    ("WITHDRAW", "WITHDRAW"),
                    ("ESCROW", "ESCROW"),
                    ("MERCHANT_SETTLEMENT", "MERCHANT_SETTLEMENT"),
                ],
                db_index=True,
                max_length=255,
            ),
        ),
    ]
