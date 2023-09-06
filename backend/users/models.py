from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Модель User"""
    email = models.EmailField(
        max_length=254,
        verbose_name=_('Электронная почта'),
        unique=True,
    )

    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError(f'''
                Пароль должен содержать как минимум 8 символов.
                Допустимые символы: буквы, цифры, символы.
    ''')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'password',
        'first_name',
        'last_name'
        ]

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ('id',)
        
    def __str__(self):
        return self.username