# crops/models.py
from django.db import models

class Crop(models.Model):
    country = models.CharField(max_length=100)
    crop = models.CharField(max_length=100)
    soil_type = models.CharField(max_length=50)
    temperature = models.CharField(max_length=20)  # keep string if ranges like "15 to 25"
    season = models.CharField(max_length=20)
    category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.crop} in {self.country}"
