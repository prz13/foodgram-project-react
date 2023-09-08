from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Follow,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

User = get_user_model()

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('id',)

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'ingredient', 'amount')
        read_only_fields = ('id',)

class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text', 'ingredients', 'tags', 'cooking_time')
        read_only_fields = ('id',)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(**tag_data)
            recipe.tags.add(tag)
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            amount = ingredient_data['amount']
            IngredientInRecipe.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)
        return recipe
