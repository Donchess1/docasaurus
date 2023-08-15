# Generated by Django 4.1.2 on 2023-08-15 05:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_alter_userprofile_locked_amount_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bankaccount",
            name="user_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
