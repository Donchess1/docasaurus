# Generated by Django 4.1.2 on 2024-04-25 04:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("merchant", "0009_remove_merchant_escrow_redirect_url_apikey"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="merchant",
            name="api_key",
        ),
    ]
