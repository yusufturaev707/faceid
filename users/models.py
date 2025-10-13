from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from pgvector.django import VectorField

from users.user_manager import UserManager
from core.models.base import BaseModel



class Role(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.IntegerField(default=0, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Rollar'
        db_table = 'role'


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(max_length=255, unique=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    telegram_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    role = models.ForeignKey('users.Role', on_delete=models.SET_NULL, blank=True, null=True)
    region = models.ForeignKey('region.Region', on_delete=models.SET_NULL, blank=True, null=True)
    img_b64 = models.TextField(blank=True, null=True)
    img_vector = VectorField(dimensions=512, blank=True, null=True)

    objects = UserManager()
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

    class Meta:
        abstract = False
        ordering = ["-id"]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'user'


class UserLog(BaseModel):
    ACTION_CHOICES = [
        ('CREATE', 'Yaratish'),
        ('UPDATE', 'Tahrirlash'),
        ('DELETE', 'O\'chirish'),
        ('VIEW', 'Ko\'rish'),
        ('LOGIN', 'Kirish'),
        ('LOGOUT', 'Chiqish'),
        ('DOWNLOAD', 'Yuklab olish'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='action_logs')
    user_role = models.CharField(max_length=50, blank=True, null=True)
    model_name = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_id = models.IntegerField()  # Mutatali objectning ID si
    old_value = models.JSONField(null=True, blank=True)  # O'zgarishdan oldin
    new_value = models.JSONField(null=True, blank=True)  # O'zgarishdan keyin
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SUCCESS', choices=STATUS_CHOICES)

    class Meta:
        db_table = 'user_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user_role} {self.user.username} - {self.action} - {self.model_name}"