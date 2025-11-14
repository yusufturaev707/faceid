from auditlog.registry import auditlog
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField
from core.models.base import BaseModel
from django.core.validators import RegexValidator

class StaffRole(BaseModel):
    name = models.CharField(max_length=20, verbose_name=_('Nomi'))
    code = models.CharField(max_length=20, verbose_name=_('Kod'))
    status = models.BooleanField(default=True, db_index=True, verbose_name=_('Status'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Rol')
        verbose_name_plural = _('Rollar')
        db_table = 'staff_role'


phone_regex = RegexValidator(
        regex=r'^\998\d{9}$',
        message="Telefon raqam: '+998901234567' formatida bo'lishi kerak"
    )

class NormalUser(BaseModel):
    GENDER_CHOICES = [
        ('M', 'Erkak'),
        ('F', 'Ayol'),
    ]

    last_name = models.CharField(max_length=255, blank=True, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=255, blank=True, verbose_name=_("Ism"))
    middle_name = models.CharField(max_length=255, blank=True, verbose_name=_("Sharif"))
    imei = models.CharField(max_length=14, unique=True, db_index=True, validators=[RegexValidator(r'^\d{14}$', 'PINFL 14 ta raqamdan iborat')], verbose_name=_("PINFL"))
    ps_ser = models.CharField(max_length=2, validators=[RegexValidator(r'^[A-Z]{2}$', 'Faqat 2 ta lotin harfi')], verbose_name=_("Seriya"))
    ps_num = models.CharField(max_length=7, validators=[RegexValidator(r'^\d{7}$', 'Faqat 7 ta raqam')], verbose_name=_("Nomer"))
    phone = models.CharField(max_length=13, blank=True, null=True, validators=[phone_regex], verbose_name=_("Telefon"))
    region = models.ForeignKey('region.Region', on_delete=models.CASCADE, verbose_name=_("Doimiy viloyat"))
    role = models.ForeignKey('access_control.StaffRole', on_delete=models.CASCADE, blank=True, verbose_name=_("Rol"))
    img_b64 = models.TextField(blank=True, null=True, verbose_name=_('Rasm'))
    img_vector = VectorField(dimensions=512, blank=True, null=True, verbose_name=_('Vector'))
    is_blacklist = models.BooleanField(default=False, verbose_name=_("Qora ro'yxatda bormi"))
    status = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    access_datetime = models.DateTimeField(blank=True)
    expired_datetime = models.DateTimeField(blank=True)
    gender = models.CharField('Jinsi', max_length=1, choices=GENDER_CHOICES, default='M')

    def __str__(self):
        return self.fio

    def image_tag(self):
        if self.img_b64:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_b64
            )
        return "(No Image)"

    image_tag.short_description = 'Rasm'

    @property
    def fio(self):
        full_name: str = f"{self.last_name} {self.first_name} {self.middle_name}"
        if not self.middle_name:
            full_name = f"{self.last_name} {self.first_name}"
        return full_name

    class Meta:
        verbose_name = 'NormalUser'
        verbose_name_plural = 'NormalUsers'
        db_table = 'normal_user'
        indexes = [
            models.Index(fields=['imei']),
        ]
        unique_together = ['ps_ser', 'ps_num']


class NormalUserLog(BaseModel):
    DIRECTION_CHOICES = [
        ('entry', 'Kirish'),
        ('exit', 'Chiqish'),
        ('unknown', 'Noma\'lum'),
    ]

    STATUS_CHOICES = [
        ('approved', 'Tasdiqlangan'),
        ('denied', 'Rad etilgan'),
        ('not_open', 'Ochilmadi'),
    ]
    normal_user = models.ForeignKey('access_control.NormalUser', on_delete=models.PROTECT, verbose_name=_("Normal User"))
    employee_no = models.CharField(max_length=100, db_index=True, blank=True, null=True, verbose_name='Student ID')
    img_face = models.TextField(blank=True, null=True, verbose_name=_("O'tgandagi rasm"))
    door = models.PositiveSmallIntegerField(default=0, verbose_name=_("Kirdi|Chiqdi eshik"))
    pass_time = models.DateTimeField(verbose_name=_("O'tgan vaqt"), blank=True, null=True,)
    ip_address = models.GenericIPAddressField(verbose_name=_("IP address"), blank=True, null=True,)
    mac_address = models.CharField(verbose_name=_("MAC address"), blank=True, null=True,)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='entry', verbose_name='Yo\'nalish')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='', db_index=True, verbose_name='Holat')

    def __str__(self):
        return f"{self.normal_user.fio}"

    def image_tag(self):
        if self.img_face:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_face
            )
        return "(No Image)"

    image_tag.short_description = 'Rasm'

    class Meta:
        verbose_name = 'NormalUserLog'
        verbose_name_plural = 'NormalUserLogs'
        db_table = 'normal_user_log'
        indexes = [
            models.Index(fields=['employee_no', '-pass_time']),
        ]


auditlog.register(StaffRole)
auditlog.register(NormalUser)
auditlog.register(NormalUserLog)