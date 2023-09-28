import base64
import re

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorite, Ingredient, Recipe, Recipe_is_ingredient,
                            Shopping_cart, Tag)
from users.models import Subscribe, User



class Base64ImageField(serializers.ImageField): # noqa
    """Сериализатор для работы и проверки изображений."""

    def to_internal_value(self, data):
        try:
            if isinstance(data, str) and data.startswith('data:image'):
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                decoded_img = base64.b64decode(imgstr)
                return ContentFile(decoded_img, name='temp.' + ext)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return super().to_internal_value(data)


class UserReadSerializer(UserSerializer):
    """Сериализатор пользователя с информацией о подписках."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = (
            request.user if request and not request.user.is_anonymous
            else None
        )

        if user and Subscribe.objects.filter(user=user, author=obj).exists():
            return True
        return False


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate(self, data):
        data = super().validate(data)

        invalid_usernames = User.INVALID_USERNAMES
        input_username = self.initial_data.get('username', '').lower()
        if input_username in (name.lower() for name in invalid_usernames):
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return data


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if not self.context['request'].user.check_password(current_password):
            raise ValidationError({'current_password': 'Неправильный пароль.'})
        if current_password == new_password:
            raise ValidationError(
                {'new_password': 'Новый пароль должен отличаться от старого.'}
            )
        return data

    def save(self):
        new_password = self.validated_data['new_password']
        user = self.context['request'].user
        user.password = make_password(new_password)
        user.save()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    image = Base64ImageField()
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для списка подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Subscribe.objects.filter(
            user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о пользователе и его подписке."""

    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def validate(self, obj):
        user = self.context['request'].user
        if user == obj:
            raise serializers.ValidationError(
                {'errors': 'Вы не можете подписаться на самого себя.'}
            )
        return obj

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Subscribe.objects.filter(
            user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегОВ."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов рецепт@."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = Recipe_is_ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения информации о рецепте."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Shopping_cart.objects.filter(
            user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов рецепта."""

    id = serializers.IntegerField()

    class Meta:
        model = Recipe_is_ingredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    author = UserReadSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'name': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'cooking_time': {'required': True},
        }

    def validate(self, data):
        required_fields = ['name', 'text', 'cooking_time']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )
        name = data.get('name')
        text = data.get('text')
        if not re.match(r'^[\w\s.,!?-]+$', name):
            raise serializers.ValidationError(
                '"Название рецепта" должно содержать только буквы.'
            )
        if len(text) < 10:
            raise serializers.ValidationError(
                '"Описание рецепта" должно содержать не менее 10 символов.'
            )
        text_exists = Recipe.objects.filter(text=text).exists()
        if text_exists:
            raise ValidationError('Рецепт с таким описанием уже существует.')
        tags = data.get('tags', [])
        ingredients = data.get('ingredients', [])
        if not tags:
            raise serializers.ValidationError('Нужно указать минимум 1 тег.')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.'
            )
        ingredient_ids = {item['id'] for item in ingredients}
        if len(ingredient_ids) != len(ingredients):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if not Ingredient.objects.filter(pk__in=ingredient_ids).exists():
            raise serializers.ValidationError(
                'Ингирдиент не существуют, '
                'выберети из существующих ингридиентов.'
            )
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        Recipe_is_ingredient.objects.bulk_create(
            [Recipe_is_ingredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        return recipe

    def update(self, instance, validated_data):
        fields_to_update = ['image', 'name', 'text', 'cooking_time']
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        for field in fields_to_update:
            setattr(instance, field, validated_data.get(
                field, getattr(instance, field))
            )
        Recipe_is_ingredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()
        ).delete()
        instance.tags.set(tags)
        Recipe_is_ingredient.objects.bulk_create(
            [Recipe_is_ingredient(
                recipe=instance,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
