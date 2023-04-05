from django.contrib import admin
from .models import Author, ResearchArea, Paper, Venue, Conference



admin.site.register(Author)
admin.site.register(Conference)
admin.site.register(Venue)

@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    filter_horizontal = ("venue", "research_area",)
