# Generated by Django 4.1.2 on 2024-04-03 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0017_userprofile_phone_number_flagged"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_merchant",
            field=models.BooleanField(default=False),
        ),
    ]
