# Generated by Django 4.1.2 on 2024-08-22 06:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("console", "0028_alter_transaction_provider"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("recipient", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("status", models.CharField(max_length=50)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "smtp_server",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("provider", models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
