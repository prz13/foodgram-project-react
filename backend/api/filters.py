# from django.contrib.auth import get_user_model
# from django_filters import rest_framework as filters
# from django_filters.rest_framework import DjangoFilterBackend

# User = get_user_model()

# class RecipeFilter(filters.FilterSet):
#     is_favorited = filters.BooleanFilter(
#         field_name='favorite__user', method='filter_is_favorited')
#     is_in_shopping_cart = filters.BooleanFilter(
#         field_name='shopping_cart__user', method='filter_is_in_shopping_cart')

#     def filter_is_favorited(self, queryset, name, value):
#         user = self.request.user
#         if value:
#             return queryset.filter(favorite__user=user)
#         return queryset

#     def filter_is_in_shopping_cart(self, queryset, name, value):
#         user = self.request.user
#         if value:
#             return queryset.filter(shopping_cart__user=user)
#         return queryset
