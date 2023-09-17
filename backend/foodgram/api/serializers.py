import base64

from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, Recipe_ingredient,
                            Shopping_cart, Tag)
from rest_framework import serializers
from users.models import Subscribe, User


class Base64ImageField(serializers.ImageField):
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
        user = request.user if request and not request.user.is_anonymous else None

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
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, data):
        data = super().validate(data)

        invalid_usernames = [
            'me',
            'set_password',
            'subscriptions',
            'subscribe'
        ]
        if self.initial_data.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return data


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        current_password = validated_data['current_password']
        new_password = validated_data['new_password']

        if not instance.check_password(current_password):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )

        if current_password == new_password:
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от старого.'}
            )

        instance.set_password(new_password)
        instance.save()

        return validated_data


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
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
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
        model = Recipe_ingredient
        fields = ('id', 'name',
                'measurement_unit', 'amount')


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
        model = Recipe_ingredient
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
        fields = '__all__'

    def validate(self, data):
        required_fields = ['name', 'text', 'cooking_time']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )

        tags = data.get('tags')
        ingredients = data.get('ingredients')

        if not tags or len(tags) < 1:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 тег.'
            )

        if not ingredients or len(ingredients) < 1:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.'
            )

        ingredient_ids = [item['id'] for item in data.get('ingredients')]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)

        Recipe_ingredient.objects.bulk_create(
            [Recipe_ingredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        Recipe_ingredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()
        ).delete()

        instance.tags.set(tags)

        Recipe_ingredient.objects.bulk_create(
            [Recipe_ingredient(
                recipe=instance,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
