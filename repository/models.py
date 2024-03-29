from django.db import models
from django.template.defaultfilters import (
    slugify,
)
from django.contrib.contenttypes.models import (
    ContentType,
)
from django.contrib.auth.models import User
from django.db.models.signals import pre_save

PUBLICATION_CHOICES = (
    ("PAPER", "Paper"),
    ("BOOK", "Book"),
    ("PROCEEDINGS", "Proceedings"),
)

SESSION_CHOICES = (
    ("WORKSHOP", "Workshop"),
    ("TUTORIAL", "Tutorial"),
)


class Author(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=250, unique=True)
    member = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user_url = models.URLField(blank=True, null=True)
    orcid = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    slug = models.SlugField()

    def __str__(self):
        return self.user_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user_name)
        return super().save(*args, **kwargs)


class ResearchArea(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.title.lower()
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class AiResource(models.Model):
    id = models.AutoField(primary_key=True)
    overview = models.TextField(default="")
    authors = models.ManyToManyField(Author, default="")
    name = models.CharField(max_length=250, unique=True)
    research_area = models.ManyToManyField(ResearchArea, default="")
    resource_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Venue(models.Model):
    id = models.AutoField(primary_key=True)
    venue_name = models.CharField(max_length=250, unique=True)
    venue_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.venue_name


class Publication(AiResource):
    slug = models.SlugField(unique=True)
    type = models.CharField(
        max_length=100,
        choices=PUBLICATION_CHOICES,
        default="Paper",
    )
    thumbnail = models.ImageField(blank=True, null=True)
    venue = models.ManyToManyField(Venue, blank=True, default="")
    citation = models.URLField(blank=True, null=True)
    pdf = models.URLField(blank=True, null=True)
    supplement = models.URLField(blank=True, null=True)
    slides = models.URLField(blank=True, null=True)
    poster = models.URLField(blank=True, null=True)
    code = models.URLField(blank=True, null=True)
    video = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Conference(Venue):
    location = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.venue_name


class Session(AiResource):
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        default=1,
    )
    type = models.CharField(
        max_length=100,
        choices=SESSION_CHOICES,
        default="Tutorial",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.conference}_{self.type}"
        return super().save(*args, **kwargs)


def check_date(sender, instance, *args, **kwargs):
    if instance.start_date > instance.end_date:
        raise ValueError("Start date must be before than end date")


pre_save.connect(check_date, sender=Session)
pre_save.connect(check_date, sender=Conference)


class Dataset(AiResource):
    link = models.URLField()
