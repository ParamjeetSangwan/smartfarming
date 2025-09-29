from django.contrib import admin
from .models import Crop  # dot works because it's a module
admin.site.register(Crop)
# Register your models here.
