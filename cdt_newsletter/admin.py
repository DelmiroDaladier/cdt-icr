from django.contrib import admin
from .models import Subscription, Newsletter
# Register your models here.

admin.site.register(Subscription)
admin.site.register(Newsletter)