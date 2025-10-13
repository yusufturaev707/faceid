from django.db import models
from pgvector.django import VectorField

from core.models.base import BaseModel


class Test(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.IntegerField(default=0, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Test'
        verbose_name_plural = 'Testlar'
        db_table = 'test'


class Shift(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    number = models.IntegerField(default=0, unique=True)
    access_time = models.TimeField()
    expire_time = models.TimeField()
    status = models.BooleanField(default=True)


class ExamStatus(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    key = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return f"Status: {self.name}"

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
        db_table = 'exam_status'


class Exam(BaseModel):
    test = models.ForeignKey('exam.Test', on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateField()
    finish_date = models.DateField()
    sm_count = models.IntegerField(default=0)
    total_taker = models.IntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    status = models.ForeignKey('exam.Status', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.test.name}"

    class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        db_table = 'exam'


class Student(BaseModel):
    exam = models.ForeignKey("exam.Exam", on_delete=models.SET_NULL, blank=True, null=True)
    zone = models.ForeignKey("region.Zone", on_delete=models.SET_NULL, blank=True, null=True)
    shift_id = models.ForeignKey("exam.Shift", on_delete=models.SET_NULL, blank=True, null=True)
    e_date = models.DateField(blank=True, null=True)
    sm = models.IntegerField(default=0)
    gr_n = models.PositiveSmallIntegerField(default=0)
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    imei = models.CharField(max_length=14, db_index=True)
    sp = models.PositiveSmallIntegerField(default=0)
    is_ready = models.BooleanField(default=True)
    is_face = models.BooleanField(default=True)
    is_image = models.BooleanField(default=True)
    is_entered = models.BooleanField(default=False)
    is_blacklist = models.BooleanField(default=False)
    is_cheating = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def fio(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        db_table = 'student'
        indexes = [
            models.Index(fields=['imei']),
        ]


class StudentPsData(BaseModel):
    student = models.OneToOneField('exam.Student', on_delete=models.CASCADE, related_name='ps_data')
    ps_ser = models.CharField(max_length=5, blank=True, null=True)
    ps_num = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=13, blank=True, null=True)
    embedding = VectorField(dimensions=512, blank=True, null=True)
    img_b64 = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.fio}"

    class Meta:
        verbose_name = 'StudentPsData'
        verbose_name_plural = 'StudentPsDatas'
        db_table = 'student_ps_data'


class StudentLog(BaseModel):
    student = models.OneToOneField("exam.Student", on_delete=models.CASCADE, related_name='logs')
    img_enter = models.TextField(blank=True, null=True)
    img_exit = models.TextField(blank=True, null=True)
    accuracy = models.PositiveSmallIntegerField(default=0)
    time_enter = models.DateTimeField(blank=True, null=True)
    time_exit = models.DateTimeField(blank=True, null=True)
    is_hand_checking = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.fio}"


    class Meta:
        verbose_name = 'StudentLog'
        verbose_name_plural = 'StudentLogs'
        db_table = 'student_log'


class StudentBlacklist(BaseModel):
    imei = models.CharField(max_length=14, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.imei}"


    class Meta:
        verbose_name = 'StudentBlacklist'
        verbose_name_plural = 'StudentBlacklists'
        db_table = 'student_blacklist'