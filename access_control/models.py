from auditlog.registry import auditlog
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from core.models.base import BaseModel



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

    USER_TYPE_CHOICES = [
        ('staff', 'Xodim'),
        ('supervisor', 'Nazoratchi'),
        ('unknown', 'Noma\'lum'),
    ]

    normal_user_id = models.PositiveBigIntegerField(default=0, verbose_name=_("User ID"))
    normal_user_type = models.CharField(verbose_name=_("User turi"), max_length=255, choices=USER_TYPE_CHOICES, default='unknown')
    zone = models.ForeignKey('region.Zone', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Bino"))
    employee_no = models.CharField(max_length=100, db_index=True, blank=True, null=True, verbose_name='Student ID')
    last_name = models.CharField(max_length=255, blank=True, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=255, blank=True, verbose_name=_("Ism"))
    middle_name = models.CharField(max_length=255, blank=True, verbose_name=_("Sharif"))
    img_face = models.TextField(blank=True, null=True, verbose_name=_("O'tgandagi rasm"))
    door = models.PositiveSmallIntegerField(default=0, verbose_name=_("Kirdi|Chiqdi eshik"))
    pass_time = models.DateTimeField(verbose_name=_("O'tgan vaqt"), blank=True, null=True,)
    ip_address = models.GenericIPAddressField(verbose_name=_("IP address"), blank=True, null=True,)
    mac_address = models.CharField(verbose_name=_("MAC address"), blank=True, null=True,)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='entry', verbose_name='Yo\'nalish')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='', db_index=True, verbose_name='Holat')

    def __str__(self):
        return f"{self.employee_no} - {self.normal_user_id}"

    def get_region(self):
        return self.zone.region.name if self.zone else ''

    get_region.short_description = 'Viloyat'

    def image_tag(self):
        if self.img_face:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_face
            )
        return "(No Image)"

    image_tag.short_description = 'Rasm'

    class Meta:
        verbose_name = 'Vakil va nazoratchi logi'
        verbose_name_plural = 'Vakil va nazoratchi loglari'
        db_table = 'normal_user_log'
        indexes = [
            models.Index(fields=['employee_no', '-pass_time']),
        ]

auditlog.register(NormalUserLog)