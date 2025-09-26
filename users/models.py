from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

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
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    telegram_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    region = models.ForeignKey('region.Region', on_delete=models.SET_NULL, blank=True, null=True)
    role = models.ForeignKey('users.Role', on_delete=models.SET_NULL, blank=True, null=True)

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