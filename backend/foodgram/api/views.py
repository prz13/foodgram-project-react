from collections import defaultdict
from datetime import datetime

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, Shopping_cart, Tag
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User

from .filters import RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          SetPasswordSerializer, SubscribeAuthorSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserCreateSerializer, UserReadSerializer)


class UserViewSet(
    viewsets.ModelViewSet,
    viewsets.GenericViewSet
):
    """Класс представления (ViewSet) для пользователей."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Пароль успешно изменен!'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        paginate_queryset = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            paginate_queryset,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        author = self.get_object()
        existing_subscription = (
            Subscribe.objects.filter(user=request.user, author=author).first()
        )
        if existing_subscription:
            return Response(
                {"error": "Вы уже подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST
            )
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
            return Response({'detail': 'Вы отписались'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Вы не были подписаны на данного автора.'},
                        status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(
    viewsets.ModelViewSet,
    viewsets.GenericViewSet
):
    """Класс представления (ViewSet) для ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class TagViewSet(
    viewsets.ModelViewSet,
    viewsets.GenericViewSet
):
    """Класс представления (ViewSet) для тегов."""

    permission_classes = (AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Класс представления (ViewSet) для рецептов."""

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
        if not Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            favorite = Favorite(user=request.user, recipe=recipe)
            favorite.save()
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт есть избранном.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def unfavorite(self, request, **kwargs):
        recipe = self.get_object()
        favorite = get_object_or_404(
            Favorite,
            user=request.user,
            recipe=recipe
        )
        favorite.delete()
        return Response(
            {'detail': 'Рецепт удален из избранного.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        recipe = self.get_object()
        if not Shopping_cart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            shopping_cart = Shopping_cart(user=request.user, recipe=recipe)
            shopping_cart.save()
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже в списке покупок.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, **kwargs):
        recipe = self.get_object()
        shopping_cart = get_object_or_404(
            Shopping_cart,
            user=request.user,
            recipe=recipe
        )
        shopping_cart.delete()
        return Response(
            {'detail': 'Рецепт удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        shopping_cart_recipes = Recipe.objects.filter(
            shopping_recipe__user=request.user
        ).annotate(
            total_amount=Sum('recipeisingredient__amount'),
            ingredient_name=F('recipeisingredient__ingredient__name'),
            measurement_unit=(
                F('recipeisingredient__ingredient__measurement_unit')
            )
        )
        shopping_cart_items = defaultdict(float)
        for recipe in shopping_cart_recipes:
            name = recipe.ingredient_name
            amount = recipe.total_amount
            shopping_cart_items[name] += amount

        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
        header = (
            f"{'Лист покупок'.center(30)}\n"
            f"Дата и время: {current_datetime}\n\n"
        )
        file_content = header + '\n'.join(shopping_cart_items)

        response = HttpResponse(file_content, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response
