from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model
from django.db import models

from embed_video.fields import EmbedVideoField


class Author(models.Model):
    user = models.CharField(max_length=250)
    user_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user


class Venue(models.Model):
    id = models.AutoField(primary_key=True)
    venue_name = models.CharField(max_length=250)
    year = models.IntegerField()
    venue_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.venue_name + ' ' + str(self.year)


class Category(models.Model):

    title = models.CharField(max_length=250)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class Post(models.Model):
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(unique=True)
    overview = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    authors = models.ManyToManyField(Author)
    thumbnail = models.ImageField(blank=True, null=True)
    categories = models.ManyToManyField(Category)
    venue = models.ManyToManyField(Venue, blank=True, default='')
    citation = models.URLField(blank=True, null=True)
    pdf = models.URLField(blank=True, null=True)
    supplement = models.URLField(blank=True, null=True)
    slides = models.URLField(blank=True, null=True)
    poster = models.URLField(blank=True, null=True)
    code = models.URLField(blank=True, null=True)
    video = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):  # new
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class Conference(models.Model):
    conference_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, unique=True)
    link = models.URLField(max_length=5000)
    location = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name
