from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, Recipe_ingredient,
                            Shopping_cart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User
from collections import defaultdict

from .filters import RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                            RecipeReadSerializer, RecipeSerializer,
                            SetPasswordSerializer, SubscribeAuthorSerializer,
                            SubscriptionsSerializer, TagSerializer,
                            UserCreateSerializer, UserReadSerializer)


"""Класс представления (ViewSet) для пользователей."""
class UserViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(detail=False,
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, 
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        author = self.get_object()
        serializer = SubscribeAuthorSerializer(
            author, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        Subscribe.objects.get_or_create(user=request.user, author=author)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        subscribe_instance = Subscribe.objects.filter(
            user=request.user, author=author).first()
        if subscribe_instance:
            subscribe_instance.delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Вы не были подписаны на данного автора.'},
                        status=status.HTTP_400_BAD_REQUEST)

"""Класс представления (ViewSet) для ингредиентов."""
class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name', )

"""Класс представления (ViewSet) для тегов."""
class TagViewSet(mixins.ListModelMixin,
                mixins.RetrieveModelMixin,
                viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

"""Класс представления (ViewSet) для рецептов."""
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPaginator
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = self.get_object()

        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            favorite = Favorite(user=request.user, recipe=recipe)
            favorite.save()
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже в избранном.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def unfavorite(self, request, **kwargs):
        recipe = self.get_object()
        favorite = get_object_or_404(Favorite, user=request.user, recipe=recipe)
        favorite.delete()
        return Response({'detail': 'Рецепт успешно удален из избранного.'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        recipe = self.get_object()

        if not Shopping_cart.objects.filter(user=request.user, recipe=recipe).exists():
            shopping_cart = Shopping_cart(user=request.user, recipe=recipe)
            shopping_cart.save()
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже в списке покупок.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, **kwargs):
        recipe = self.get_object()
        shopping_cart = get_object_or_404(Shopping_cart, user=request.user, recipe=recipe)
        shopping_cart.delete()
        return Response({'detail': 'Рецепт успешно удален из списка покупок.'},
                        status=status.HTTP_204_NO_CONTENT)


    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        shopping_cart_recipes = Recipe.objects.filter(
            shopping_recipe__user=request.user
        )

        shopping_cart_items = defaultdict(float)

        for recipe in shopping_cart_recipes:
            ingredients = Recipe_ingredient.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                name = ingredient.ingredient.name
                amount = ingredient.amount
                measurement_unit = ingredient.ingredient.measurement_unit
                shopping_cart_items[name] += amount

        shopping_cart_items_formatted = [
            f"{name} - {amount} {measurement_unit}"
            for name, amount in shopping_cart_items.items()
        ]

        file_content = '\n'.join(shopping_cart_items_formatted)
        response = HttpResponse(file_content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
