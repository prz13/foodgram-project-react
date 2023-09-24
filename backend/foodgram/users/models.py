from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель User"""

    email = models.EmailField(
        max_length=254,
        verbose_name='Электронная почта',
        unique=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'password',
        'first_name',
        'last_name'
    ]

    class Meta:
        verbose_name = ('Пользователь')
        verbose_name_plural = ('Пользователи')
        ordering = ('id',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Подписан'
    )

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'Подписка на авторов'
        verbose_name_plural = 'Подписки на авторов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]
