# Generated by Django 3.2.12 on 2023-06-26 09:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cdt_newsletter", "0004_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="publication_date",
            field=models.DateField(null=True),
        ),
    ]
