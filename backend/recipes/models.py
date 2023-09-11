from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()

class Recipe(models.Model):
    """Модель рецепт"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=('Автор публикации')
    )
    title = models.CharField(('Название'), max_length=255)
    image = models.ImageField(('Картинка'), upload_to='recipes/')
    description = models.TextField(('Текстовое описание'))
    ingredients = models.ManyToManyField(
        'Ingredient',  # 'Ingredient' - предполагаемая модель ингредиента
        through='IngredientInRecipe',
        verbose_name=('Ингредиенты')
    )
    tags = models.ManyToManyField(
        'Tag',  # 'Tag' - предполагаемая модель тега
        verbose_name=('Теги')
    )
    cooking_time = models.PositiveIntegerField(
        ('Время приготовления (в минутах)'),
        validators=[MinValueValidator(limit_value=-1, message='Мин. значение -1!')]
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')


class Ingredient(models.Model):
    """Модель ингридиенты"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название ингредиента'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Количество'
    )
    unit_of_measurement = models.CharField(
        max_length=20,
        verbose_name='Единицы измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

class Tag(models.Model):
    """Модель тег"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
        unique=True  
    )
    color_code = models.CharField(
        max_length=7,  
        verbose_name='Цветовой код',
        unique=False  
    )
    slug = models.SlugField(
        max_length=255,
        verbose_name='Slug',
        unique=True  
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

class IngredientInRecipe(models.Model):
    """Ингирдиенты в рецепте модель для связки"""
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Количество'
    )

    def __str__(self):
        return (
    f'{self.ingredient.name} '
    f'({self.amount} {self.ingredient.unit_of_measurement})'
)

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'