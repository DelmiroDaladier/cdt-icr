from django.contrib import admin
from .models import Subscription, Newsletter, Announcement
# Register your models here.

admin.site.register(Subscription)
admin.site.register(Newsletter)
admin.site.register(Announcement)