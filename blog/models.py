from django.db import models
from django.template.defaultfilters import slugify
from repository.models import AiResource, Author, ResearchArea
# Create your models here.


class BlogPost(AiResource):
    slug = models.SlugField(unique=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)
