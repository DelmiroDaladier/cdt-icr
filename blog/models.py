from django.db import models
from django.template.defaultfilters import slugify
from repository.models import Author, Category
# Create your models here.


class BlogPost(models.Model):
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(unique=True)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    authors = models.ManyToManyField(Author)
    categories = models.ManyToManyField(Category)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)
