from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

from rest_framework.decorators import action
from rest_framework.response import Response


User = get_user_model()

class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        return Response({"message": "Вы подписанны."})
