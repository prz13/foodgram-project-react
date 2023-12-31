import csv
import logging
import os

from django.core.management.base import BaseCommand
from foodgram import settings
from recipes.models import Ingredient
from tqdm import tqdm

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load ingredients to DB"

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'ingredients.csv')

        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)

                ingredients = [
                    Ingredient(name=row[0], measurement_unit=row[1])
                    for row in tqdm(reader,
                                    desc="Loading ingredients",
                                    unit=" row")
                ]

                Ingredient.objects.all().delete()
                Ingredient.objects.bulk_create(ingredients)
                self.stdout.write(self.style.SUCCESS("Uploaded successfully!"))
        except FileNotFoundError:
            logger.error("File not found: ingredients.csv")
        except csv.Error as e:
            logger.error(f"CSV Error: {e}")
