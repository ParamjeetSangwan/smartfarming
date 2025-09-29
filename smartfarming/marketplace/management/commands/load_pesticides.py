import os
import csv
from django.core.management.base import BaseCommand
from marketplace.models import Pesticide

class Command(BaseCommand):
    help = 'Load pesticides from CSV file'

    def handle(self, *args, **options):
        file_path = os.path.join('marketplace', 'data', 'pesticides.csv')
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Pesticide.objects.create(
                    name=row['Name'],
                    category=row['Category'],
                    type=row['Type'],
                    description=row['Description'],
                    price=row['Price'],
                    image_url=row['Image URL']
                )
        self.stdout.write(self.style.SUCCESS('Successfully loaded pesticides.'))
