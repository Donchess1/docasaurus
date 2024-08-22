# Generated by Django 4.1.2 on 2024-08-22 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("console", "0029_emaillog"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemConfig",
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
                ("key", models.CharField(max_length=100, unique=True)),
                ("value", models.CharField(max_length=255)),
                ("valid_choices", models.JSONField(blank=True, default=list)),
            ],
            options={
                "verbose_name": "System Configuration",
                "verbose_name_plural": "System Configurations",
            },
        ),
    ]
