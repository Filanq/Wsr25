from django.contrib import admin
from django.contrib.admin import register
from .models import User


admin.site.register(User)
