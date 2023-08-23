# Generated by Django 4.1.2 on 2023-08-23 02:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("console", "0009_remove_lockedamount_seller_lockedamount_seller_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="lockedamount",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="lockedamount",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
