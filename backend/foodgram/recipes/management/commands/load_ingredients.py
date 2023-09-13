import csv
import os
import logging
from foodgram import settings
from tqdm import tqdm  # Импорт tqdm

from django.core.management.base import BaseCommand
from recipes.models import Ingredient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Load ingredients to DB"

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'ingredients.csv')

        try:
            with open(path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Пропустить заголовок

                ingredients = [
                    Ingredient(name=row[0], measurement_unit=row[1])
                    for row in tqdm(reader, desc="Loading ingredients", unit=" row")
                ]

                Ingredient.objects.all().delete()  # Очистить существующие записи
                Ingredient.objects.bulk_create(ingredients)
                self.stdout.write(self.style.SUCCESS("The ingredients have been loaded successfully."))
        except FileNotFoundError:
            logger.error("File not found: ingredients.csv")
        except csv.Error as e:
            logger.error(f"CSV Error: {e}")
