# Generated by Django 3.2.12 on 2023-04-03 12:23

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "repository",
            "0003_post_name",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="post",
            name="title",
        ),
    ]
