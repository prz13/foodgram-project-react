from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsAdminOrReadOnly(BasePermission):
    """Пользователи с правами Admin и только чтение"""

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)

class IsAuthorOrReadOnly(BasePermission):
    """Для авторов"""

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
