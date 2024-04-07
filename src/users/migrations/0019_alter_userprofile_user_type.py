# Generated by Django 4.1.2 on 2024-04-03 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0018_customuser_is_merchant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("BUYER", "BUYER"),
                    ("SELLER", "SELLER"),
                    ("CONTRACTOR", "CONTRACTOR"),
                    ("MERCHANT", "MERCHANT"),
                ],
                max_length=255,
            ),
        ),
    ]
