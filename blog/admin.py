from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class PostAdmin(admin.ModelAdmin):
    filter_horizontal = ("authors",)
