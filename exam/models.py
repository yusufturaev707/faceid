from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from pgvector.django import VectorField
from auditlog.registry import auditlog
from core.models.base import BaseModel
from region.models import Zone
from django.utils.translation import gettext_lazy as _



class Test(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Nom"))
    code = models.IntegerField(default=0, unique=True, verbose_name=_("Kod"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Test turi'
        verbose_name_plural = 'Test turlari'
        db_table = 'test'


class Shift(BaseModel):
    name = models.CharField(max_length=20, unique=True, verbose_name=_("Nom"))
    number = models.IntegerField(default=0, unique=True, verbose_name=_("Nomer"))
    status = models.BooleanField(default=True, verbose_name=_("Holat"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Smena'
        verbose_name_plural = 'Smenalar'
        db_table = 'shift'


class ExamShift(BaseModel):
    exam = models.ForeignKey('exam.Exam', on_delete=models.CASCADE, related_name='exams', verbose_name=_("Tadbir"))
    sm = models.ForeignKey('exam.Shift', on_delete=models.CASCADE, related_name='shifts', verbose_name=_("Smena"))
    access_time = models.TimeField(verbose_name=_("Ruxsat vaqti"))
    expire_time = models.TimeField(verbose_name=_("Yopilish vaqti"))

    def __str__(self):
        return f"{self.sm.name} - {self.exam.test.name}"

    class Meta:
        verbose_name = 'Kirish ruxsati'
        verbose_name_plural = 'Kirish ruxsati'
        db_table = 'exam_sm'


class ExamState(BaseModel):
    name = models.CharField(max_length=120, unique=True, verbose_name=_("Nom"))
    key = models.CharField(max_length=120, unique=True, verbose_name=_("Kod"))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Tadbir holati'
        verbose_name_plural = 'Tadbir holatlari'
        db_table = 'exam_state'


class Exam(BaseModel):
    test = models.ForeignKey('exam.Test', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Test turi"))
    hash_key = models.CharField(max_length=120, unique=True, verbose_name=_("Kod"))
    start_date = models.DateField(verbose_name=_("Birinchi kun"))
    finish_date = models.DateField(verbose_name=_("Oxirgi kun"))
    sm_count = models.IntegerField(default=0, verbose_name=_("Kun davomidagi smena soni"))
    total_taker = models.IntegerField(default=0, verbose_name=_("Test topshiruvchilar soni"))
    is_finished = models.BooleanField(default=False, verbose_name=_("Tugadimi"))
    status = models.ForeignKey('exam.ExamState', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Holat"))

    def __str__(self):
        return f"{self.test.name}"

    class Meta:
        verbose_name = 'Tadbir'
        verbose_name_plural = 'Tadbirlar'
        db_table = 'exam'


class Student(BaseModel):
    exam = models.ForeignKey("exam.Exam", on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Tadbir"))
    zone = models.ForeignKey("region.Zone", on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Bino"))
    e_date = models.DateField(blank=True, null=True, verbose_name=_("Imtihon topshirish kuni"))
    sm = models.IntegerField(default=0, verbose_name=_("Smena"))
    gr_n = models.PositiveSmallIntegerField(default=0, verbose_name=_("Guruh"))
    last_name = models.CharField(max_length=255, verbose_name=_("Familiya"))
    first_name = models.CharField(max_length=255, verbose_name=_("Ismi"))
    middle_name = models.CharField(max_length=255, verbose_name=_("Sharif"))
    imei = models.CharField(max_length=14, db_index=True, verbose_name=_("Jshshir"))
    sp = models.PositiveSmallIntegerField(default=0, verbose_name=_("O'rni"))
    is_ready = models.BooleanField(default=True, verbose_name=_("Tayyor"))
    is_face = models.BooleanField(default=True, verbose_name=_("Yuz aniqlanganmi"))
    is_image = models.BooleanField(default=True, verbose_name=_("Rasmi bormi"))
    is_entered = models.BooleanField(default=False, verbose_name=_("Turniketdan kirdimi"))
    is_blacklist = models.BooleanField(default=False, verbose_name=_("Qora ro'yxatda bormi"))
    is_cheating = models.BooleanField(default=False, verbose_name=_("Chetlashdimi"))
    s_code = models.BigIntegerField(unique=True, verbose_name=_("UserID"))

    def __str__(self):
        return self.fio

    @property
    def fio(self):
        full_name: str = f"{self.last_name} {self.first_name} {self.middle_name}"
        if not self.middle_name:
            full_name = f"{self.last_name} {self.first_name}"
        return full_name

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Studentlar'
        db_table = 'student'
        indexes = [
            models.Index(fields=['imei']),
        ]


class StudentPsData(BaseModel):
    student = models.OneToOneField('exam.Student', on_delete=models.CASCADE, related_name='ps_data', verbose_name=_("Student"))
    ps_ser = models.CharField(max_length=5, blank=True, null=True, verbose_name=_("Seriya"))
    ps_num = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Nomer"))
    phone = models.CharField(max_length=13, blank=True, null=True, verbose_name=_("Telefon"))
    embedding = VectorField(dimensions=512, blank=True, null=True, verbose_name=_("Vector"))
    img_b64 = models.TextField(blank=True, null=True, verbose_name=_("Rasm"))

    def __str__(self):
        return f"EXAM | StudentPsData - {self.student.fio}"

    def image_tag(self):
        if self.img_b64:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_b64
            )
        return "(No Image)"

    image_tag.short_description = 'Rasm'

    class Meta:
        verbose_name = 'Pasport malumot'
        verbose_name_plural = 'Pasport malumotlari'
        db_table = 'student_ps_data'


class StudentLog(BaseModel):
    DIRECTION_CHOICES = [
        ('entry', 'Enter'),
        ('exit', 'Exit'),
        ('unknown', 'Unknown'),
    ]

    STATUS_CHOICES = [
        ('approved', 'Opened'),
        ('denied', 'Deny'),
        ('not_open', 'Not Opened'),
    ]

    student = models.ForeignKey("exam.Student", on_delete=models.SET_NULL, related_name='student_logs', blank=True, null=True, verbose_name=_("Student"))
    employee_no = models.CharField(max_length=100, db_index=True, verbose_name='Student ID')
    img_face = models.TextField(blank=True, null=True, verbose_name=_("O'tgandagi rasm"))
    door = models.PositiveSmallIntegerField(default=0, verbose_name=_("Kirdi|Chiqdi eshik"))
    accuracy = models.PositiveSmallIntegerField(default=0, verbose_name=_("O'xshashlik"))
    pass_time = models.DateTimeField(verbose_name=_("O'tgan vaqt"))
    ip_address = models.GenericIPAddressField(verbose_name=_("IP address"))
    mac_address = models.CharField(verbose_name=_("MAC address"))
    is_hand_checked = models.BooleanField(default=False, verbose_name=_("Qo'lda tekshirilgan"))
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='entry', verbose_name='Yo\'nalish')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='', db_index=True, verbose_name='Holat')
    requires_verification = models.BooleanField(default=False, db_index=True, verbose_name='Tasdiqlash kerakmi')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Vaqt')

    def __str__(self):
        return f"{self.student.fio}"

    def image_tag(self):
        if self.img_face:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:150px;" />',
                self.img_face
            )
        return "(No Image)"

    image_tag.short_description = 'Rasm'

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Loglar'
        db_table = 'student_log'
        indexes = [
            models.Index(fields=['-timestamp', 'status']),
            models.Index(fields=['employee_no', '-timestamp']),
        ]

    def mark_as_processed(self, approved=True):
        """Qayta ishlangan deb belgilash"""
        self.status = 'approved' if approved else 'denied'
        self.save()


class Reason(BaseModel):
    name = models.CharField(max_length=255, verbose_name=_("Nomi"))
    key = models.PositiveSmallIntegerField(default=0, verbose_name=_("Key"))
    status = models.BooleanField(default=True, verbose_name=_("Holat"))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Sabab'
        verbose_name_plural = 'Sabablar'
        db_table = 'reason'


class Cheating(BaseModel):
    student = models.ForeignKey("exam.Student", on_delete=models.SET_NULL, blank=True, null=True, help_text="Student")
    reason = models.ForeignKey('exam.Reason', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Chetlatish sababi"))
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, blank=True, null=True, help_text="Chetlatgan vakil")
    imei = models.CharField(max_length=14, db_index=True, verbose_name=_("Jshshir"), validators=[RegexValidator(r'^\d{14}$', 'PINFL 14 ta raqamdan iborat')])
    pic = models.ImageField(upload_to='cheating/', blank=True, null=True, verbose_name=_("Rasm"))

    def __str__(self):
        return f"{self.imei}"

    class Meta:
        verbose_name = "Chetlatilgan student"
        verbose_name_plural = "Chetlatilgan studentlar"
        db_table = 'cheating'



class StudentBlacklist(BaseModel):
    imei = models.CharField(max_length=14, db_index=True, unique=True, verbose_name=_("Jshshir"))
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Izoh"))

    def __str__(self):
        return f"{self.imei}"


    class Meta:
        verbose_name = "Qora ro'yxat"
        verbose_name_plural = "Qora ro'yxatdagilar"
        db_table = 'student_blacklist'


class ExamZoneSwingBar(BaseModel):
    exam = models.ForeignKey('exam.Exam', on_delete=models.CASCADE, help_text="Exam")
    sb = models.ForeignKey('region.SwingBarrier', on_delete=models.CASCADE, help_text="SwingBarrier")
    unpushed_users_imei = models.TextField(blank=True, null=True, verbose_name=_("Qolib ketgan student pinfllari"))
    unpushed_images_imei = models.TextField(blank=True, null=True, verbose_name=_("Qolib ketgan student rasmlari"))
    real_count = models.BigIntegerField(default=0, verbose_name=_("Real count"))
    pushed_user_count = models.BigIntegerField(default=0, verbose_name=_("Yuklangan studentlar soni"))
    pushed_image_count = models.BigIntegerField(default=0, verbose_name=_("Yuklangan ramlar soni"))
    err_user_count = models.BigIntegerField(default=0, verbose_name=_("Yuklanmagan studentlar soni"))
    err_image_count = models.BigIntegerField(default=0, verbose_name=_("Yuklanmagan rasmlar soni"))
    status = models.BooleanField(default=False, verbose_name=_("Holat"))

    def save(self, *args, **kwargs):
        if self.real_count == self.pushed_user_count and self.real_count == self.pushed_image_count and self.real_count > 0:
            self.status = True
        else:
            self.status = False
        super(ExamZoneSwingBar, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.exam.id} | {self.sb.zone.region.name} | {self.sb.zone.name} | {self.real_count}"

    class Meta:
        verbose_name = _('Tadbirga biriktirilgan turniket')
        verbose_name_plural = _('Tadbirga biriktirilgan turniketlar')
        db_table = 'exam_zone_swing_bar'


auditlog.register(Cheating)
auditlog.register(Exam)
auditlog.register(ExamShift)
auditlog.register(ExamState)
auditlog.register(Reason)
auditlog.register(Shift)
auditlog.register(Student)
auditlog.register(StudentBlacklist)
auditlog.register(StudentLog)
auditlog.register(StudentPsData)
auditlog.register(Test)
auditlog.register(ExamZoneSwingBar)