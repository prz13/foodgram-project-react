from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewSet)
router.register('users', views.UserViewSet)
router.register('ingredients', views.IngredientViewSet)

urlpatterns = router.urls

urlpatterns = router.urls + [
    path('auth/', include('djoser.urls.authtoken')),
]
