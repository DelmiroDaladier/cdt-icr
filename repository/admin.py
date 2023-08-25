from django.contrib import admin
from .models import (
    Author,
    ResearchArea,
    Publication,
    Venue,
    Conference,
    Session,
    Dataset,
)

admin.site.register(Author)
admin.site.register(Conference)
admin.site.register(Venue)
admin.site.register(Session)
admin.site.register(Dataset)


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    filter_horizontal = (
        "venue",
        "research_area",
    )
