from django.contrib import admin
from .models import User, Subscribe

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'pk', 'email', 'first_name', 'last_name')
    list_editable = ('email', 'first_name', 'last_name')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = None

@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_editable = ('user', 'author')
    empty_value_display = None
