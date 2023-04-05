from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType


class Author(models.Model):
    user_id = models.AutoField(primary_key=True)
    user = models.CharField( max_length=250, unique=True)
    user_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user

class ResearchArea(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class AiResource(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, unique=True)
    authors = models.ManyToManyField(Author, default='')
    research_area = models.ManyToManyField(ResearchArea, default='')

    class Meta:
        abstract = True

class Venue(models.Model):
    id = models.AutoField(primary_key=True)
    venue_name = models.CharField(max_length=250, unique=True)
    venue_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.venue_name

class Paper(AiResource):
    slug = models.SlugField(unique=True)
    overview = models.TextField()
    thumbnail = models.ImageField(blank=True, null=True)
    venue = models.ManyToManyField(Venue, blank=True, default='')
    citation = models.URLField(blank=True, null=True)
    pdf = models.URLField(blank=True, null=True)
    supplement = models.URLField(blank=True, null=True)
    slides = models.URLField(blank=True, null=True)
    poster = models.URLField(blank=True, null=True)
    code = models.URLField(blank=True, null=True)
    video = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs): 
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Conference(AiResource):
    link = models.URLField(max_length=5000)
    location = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Session(AiResource):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

class Announcement(AiResource):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Dataset(AiResource):
    link = models.URLField()