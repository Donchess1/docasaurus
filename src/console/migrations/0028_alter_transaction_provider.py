# Generated by Django 4.1.2 on 2024-08-21 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("console", "0027_alter_transaction_provider"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="provider",
            field=models.CharField(
                choices=[
                    ("FLUTTERWAVE", "FLUTTERWAVE"),
                    ("PAYSTACK", "PAYSTACK"),
                    ("BLUSALT", "BLUSALT"),
                    ("TERRASWITCH", "TERRASWITCH"),
                    ("STRIPE", "STRIPE"),
                    ("MYBALANCE", "MYBALANCE"),
                ],
                db_index=True,
                max_length=255,
            ),
        ),
    ]
