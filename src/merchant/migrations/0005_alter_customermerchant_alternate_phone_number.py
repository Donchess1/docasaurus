# Generated by Django 4.1.2 on 2024-04-08 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("merchant", "0004_customer_customermerchant_customer_merchants_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customermerchant",
            name="alternate_phone_number",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
