from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from auditlog.registry import auditlog
from django.db import models
from pgvector.django import VectorField

from users.user_manager import UserManager
from core.models.base import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(max_length=255, unique=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    telegram_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    region = models.ForeignKey('region.Region', on_delete=models.SET_NULL, blank=True, null=True)
    img_b64 = models.TextField(blank=True, null=True)
    img_vector = VectorField(dimensions=512, blank=True, null=True)

    objects = UserManager()
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.groups.filter(name='Admin').exists()

    @property
    def is_central(self):
        return self.groups.filter(name='Markaz').exists()

    @property
    def is_delegate(self):
        return self.groups.filter(name='Vakil').exists()

    @property
    def is_user(self):
        return self.groups.filter(name='User').exists()

    class Meta:
        abstract = False
        ordering = ["-id"]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'user'


auditlog.register(User)