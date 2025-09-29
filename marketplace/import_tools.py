import csv
from marketplace.models import Tool
from django.core.files.base import ContentFile
import urllib.request

def import_tools_from_csv():
    csv_path = 'marketplace/data/tools.csv'  # Update if path differs

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Name']
            description = row['Description']
            price = row['Price']
            category = row['Category']
            image_url = row['Image URL']

            tool = Tool(name=name, description=description, price=price, category=category)

            if image_url:
                try:
                    result = urllib.request.urlretrieve(image_url)
                    image_name = image_url.split("/")[-1]
                    with open(result[0], 'rb') as f:
                        tool.image.save(image_name, ContentFile(f.read()), save=False)
                except Exception as e:
                    print(f"⚠️ Image download failed for {name}: {e}")

            tool.save()

    print("✅ Tools imported successfully!")
