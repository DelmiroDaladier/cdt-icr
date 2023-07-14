from django.contrib import admin
from .models import Subscription, Newsletter, Announcement, Event


# Register your models here.

admin.site.register(Subscription)
admin.site.register(Newsletter)
admin.site.register(Announcement)
admin.site.register(Event)