# Generated by Django 4.1.2 on 2024-04-11 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="content",
            field=models.TextField(blank=True, null=True),
        ),
    ]
