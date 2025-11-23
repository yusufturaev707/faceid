from auditlog.registry import auditlog
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField
from core.models.base import BaseModel
from django.core.validators import RegexValidator


phone_regex = RegexValidator(
        regex=r'^998\d{9}$',
        message="Telefon raqam: '998901234567' formatida bo'lishi kerak"
    )


class Staff(BaseModel):
    GENDER_CHOICES = [
        ('M', 'Erkak'),
        ('F', 'Ayol'),
    ]

    last_name = models.CharField(max_length=255, blank=True, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=255, blank=True, verbose_name=_("Ism"))
    middle_name = models.CharField(max_length=255, blank=True, verbose_name=_("Sharif"))
    imei = models.CharField(max_length=14, unique=True, db_index=True, validators=[RegexValidator(r'^\d{14}$', 'PINFL 14 ta raqamdan iborat')], verbose_name=_("PINFL"))
    ps_ser = models.CharField(max_length=2, validators=[RegexValidator(r'^[A-Za-z]{2}$', 'Faqat 2 ta katta lotin harfi')], verbose_name=_("Seriya"))
    ps_num = models.CharField(max_length=7, validators=[RegexValidator(r'^\d{7}$', 'Faqat 7 ta raqam')], verbose_name=_("Nomer"))
    phone = models.CharField(max_length=12, blank=True, null=True, validators=[phone_regex], verbose_name=_("Telefon"))
    region = models.ForeignKey('region.Region', on_delete=models.CASCADE, verbose_name=_("Doimiy viloyat"))
    img_b64 = models.TextField(blank=True, null=True, verbose_name=_('Rasm'))
    img_vector = VectorField(dimensions=512, blank=True, null=True, verbose_name=_('Vector'))
    gender = models.CharField('Jinsi', max_length=1, choices=GENDER_CHOICES, default='M')
    status = models.BooleanField(default=True, verbose_name=_('Aktiv'))

    def __str__(self):
        return self.fio

    def image_tag(self):
        if self.img_b64:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_b64
            )
        return "(No Image)"

    @property
    def fio(self):
        full_name: str = f"{self.last_name} {self.first_name} {self.middle_name}"
        if not self.middle_name:
            full_name = f"{self.last_name} {self.first_name}"
        return full_name

    class Meta:
        verbose_name = 'Xodim'
        verbose_name_plural = 'Xodimlar'
        db_table = 'staff'
        indexes = [
            models.Index(fields=['imei']),
        ]
        unique_together = ['ps_ser', 'ps_num']


class Supervisor(BaseModel):
    GENDER_CHOICES = [
        ('M', 'Erkak'),
        ('F', 'Ayol'),
    ]

    last_name = models.CharField(max_length=50, blank=True, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=50, blank=True, verbose_name=_("Ism"))
    middle_name = models.CharField(max_length=50, blank=True, verbose_name=_("Sharif"))
    imei = models.CharField(max_length=14, db_index=True, unique=True, validators=[RegexValidator(r'^\d{14}$', 'PINFL 14 ta raqamdan iborat')], verbose_name=_("PINFL"))
    ps_ser = models.CharField(max_length=2, validators=[RegexValidator(r'^[A-Z]{2}$', 'Faqat 2 ta lotin harfi')], verbose_name=_("Seriya"))
    ps_num = models.CharField(max_length=7, validators=[RegexValidator(r'^\d{7}$', 'Faqat 7 ta raqam')], verbose_name=_("Nomer"))
    region = models.ForeignKey('region.Region', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Doimiy"))
    img_b64 = models.TextField(blank=True, null=True, verbose_name=_('Rasm'))
    img_vector = VectorField(dimensions=512, blank=True, null=True, verbose_name=_('Vector'))
    gender = models.CharField('Jinsi', max_length=1, choices=GENDER_CHOICES, default='M')
    status = models.BooleanField(default=True, verbose_name=_('Aktiv'))

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
        verbose_name = 'Nazoratchi'
        verbose_name_plural = 'Nazoratchilar'
        db_table = 'supervisor'


class EventSupervisor(BaseModel):
    supervisor = models.ForeignKey('access_control.Supervisor', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('Nazoratchi'))
    exam = models.ForeignKey('exam.Exam', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('Tadbir'))
    zone = models.ForeignKey('region.Zone', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Bino"))
    category_key = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Toifa kodi"))
    category_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Toifa nomi"))
    test_date = models.DateField(null=True, blank=True, verbose_name=_("Test date"))
    sm = models.PositiveSmallIntegerField(default=0, verbose_name=_("Smena"))
    group_n = models.PositiveSmallIntegerField(default=0, verbose_name=_("Guruh"))
    access_datetime = models.DateTimeField(blank=True, verbose_name=_("Boshlanish vaqti"))
    expired_datetime = models.DateTimeField(blank=True, verbose_name=_("Tugash vaqti"))
    is_participated = models.BooleanField(default=False, verbose_name=_("Davomat"))

    def __str__(self):
        return f"{self.supervisor.fio} - {self.exam.test.name}|{self.exam.start_date}"

    class Meta:
        verbose_name = 'Biriktirilgan nazoratchi'
        verbose_name_plural = 'Biriktirilgan nazoratchilar'
        db_table = 'event_supervisor'


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


auditlog.register(Staff)
auditlog.register(Supervisor)
auditlog.register(EventSupervisor)
auditlog.register(NormalUserLog)