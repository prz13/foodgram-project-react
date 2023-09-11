from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from drf_extra_fields.fields import Base64ImageField
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import UniqueConstraint
from recipes.models import Recipe, Ingredient, Tag, IngredientInRecipe
from users.models import Follow, User
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from .filters import RecipeFilter
from api.serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    TagSerializer,
    IngredientSerializer,
    IngredientInRecipeSerializer,
    RecipeSerializer
)
from djoser.views import UserViewSet

User = get_user_model()

class RecipeFilter(filters.FilterSet):
    """Вьюсет фильтр для работы с рецептами"""
    is_favorited = filters.BooleanFilter(
        field_name='favorite__user', method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopping_cart__user', method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(shopping_cart__user=user)
        return queryset

class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователем"""
    queryset = User.objects.all()

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        target_user = self.get_object()

        if request.user == target_user:
            return Response('Вы не можете подписаться на себя!',
                            status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(user=request.user, author=target_user).exists():
            return Response('Вы уже подписаны на этого пользователя!',
                            status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=request.user, author=target_user)
        return Response('Подписка успешно добавлена',
                        status=status.HTTP_201_CREATED)

class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для работы с ингирдиентами"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name',)

class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @staticmethod
    def ingredients_to_txt(ingredients):
        shopping_list = 'Список покупок:\n'
        for ingredient in ingredients:
            shopping_list += f"{ingredient['ingredient__name']} - {ingredient['sum']} {ingredient['ingredient__measurement_unit']}\n"
        return shopping_list

    def generate_pdf_shopping_list(self, ingredients):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica", 12)
        p.drawString(100, 750, "Список покупок:")
        y = 730
        for ingredient in ingredients:
            y -= 15
            p.drawString(100, y, f"{ingredient['ingredient__name']} - {ingredient['sum']} {ingredient['ingredient__measurement_unit']}")
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)

        file_type = request.query_params.get('file_type', 'txt')
        if file_type == 'pdf':
            buffer = self.generate_pdf_shopping_list(ingredients)
            response = HttpResponse(
                buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
            buffer.close()
            return response
        else:
            response = HttpResponse(shopping_list, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
            return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': f'Рецепт "{recipe.name}" уже есть в списке покупок.'},
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = AddFavoritesSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = ShoppingCart.objects.filter(user=user, recipe__id=pk)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': f'Рецепта "{recipe.name}" нет в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

# class ShoppingListViewSet(ModelViewSet):
#     """Вьюсет для работы с покупками"""
#     queryset = ShoppingCart.objects.all()
#     serializer_class = ShoppingListSerializer
#     permission_classes = (IsAuthenticated,)
