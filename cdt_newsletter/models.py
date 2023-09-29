import datetime

from django.db import models

# Create your models here.


class Subscription(models.Model):
    email = models.EmailField(null=True)
    date = models.DateTimeField(auto_now_add=True)


class Newsletter(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(
        max_length=100, null=True
    )
    tldr = models.TextField(max_length=200)
    text = models.TextField()
    created_at = models.DateField(
        auto_now_add=True
    )
    modified_at = models.DateField(auto_now=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title:
            self.created_at = (
                datetime.datetime.now().strftime(
                    "%d-%m-%Y"
                )
            )
            self.title = f"cdt_newsletter_{self.created_at}"
        return super().save(*args, **kwargs)


class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(
        max_length=250, null=True
    )
    text = models.TextField(max_length=500)
    created_at = models.DateField(
        auto_now_add=True
    )
    modified_at = models.DateField(auto_now=True)
    published = models.BooleanField(default=False)
    publication_date = models.DateField(
        default=None, blank=True, null=True
    )

    def __str__(self):
        return self.title


class Event(Announcement):
    date = models.DateField()

    def __str__(self):
        return self.title
