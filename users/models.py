from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from auditlog.registry import auditlog
from django.db import models
from pgvector.django import VectorField
from django.utils.translation import gettext_lazy as _

from users.user_manager import UserManager
from core.models.base import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(max_length=255, unique=True, verbose_name=_('username'))
    last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Ism"))
    middle_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Sharif"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    telegram_id = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name=_('TelegramID'))
    region = models.ForeignKey('region.Region', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('Viloyat'))
    img_b64 = models.TextField(blank=True, null=True, verbose_name=_('Rasm'))
    img_vector = VectorField(dimensions=512, blank=True, null=True, verbose_name=_('Vector'))

    objects = UserManager()
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
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
        verbose_name = 'Xodim'
        verbose_name_plural = 'Xodimlar'
        db_table = 'user'



class Role(Group):
    class Meta:
        # Group modelidan foydalanadiganligini bildiradi
        proxy = True

        # Admin panelidagi nomlari
        verbose_name = _("Rol")
        verbose_name_plural = _("Rollar")


auditlog.register(User)
auditlog.register(Role)