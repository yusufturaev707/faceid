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


class Status(BaseModel):
    name = models.CharField(max_length=120, unique=True, blank=False, null=False)
    key = models.CharField(max_length=120, unique=True, blank=False, null=False)

    def __str__(self):
        return f"Status: {self.name}"

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
        db_table = 'status'


class Exam(BaseModel):
    start_date = models.DateField(blank=True, null=True)
    finish_date = models.DateField(blank=True, null=True)
    sm_count = models.IntegerField(default=0)
    test = models.ForeignKey('exam.Test', on_delete=models.SET_NULL, blank=True, null=True)
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
    region = models.ForeignKey("region.Region", on_delete=models.SET_NULL, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    test_day = models.CharField(max_length=20, blank=True, null=True)
    e_date = models.DateField(blank=True, null=True)
    e_time = models.CharField(max_length=8, blank=True, null=True)
    sm = models.IntegerField(default=0)
    imei = models.CharField(max_length=14, db_index=True)
    group = models.PositiveSmallIntegerField(default=0)
    seat = models.PositiveSmallIntegerField(default=0)
    embedding = VectorField(dimensions=512, blank=True, null=True)
    img_b64 = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_face = models.BooleanField(default=True)
    is_image = models.BooleanField(default=True)
    is_entered = models.BooleanField(default=False)
    subject_id = models.IntegerField(blank=True, null=True)
    subject_name = models.CharField(max_length=255, blank=True, null=True)
    lang_id = models.IntegerField(blank=True, null=True)
    level_id = models.IntegerField(blank=True, null=True)
    phone = models.CharField(max_length=13, blank=True, null=True)
    ps_ser = models.CharField(max_length=5, blank=True, null=True)
    ps_number = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        db_table = 'student'
        indexes = [
            models.Index(fields=['imei']),
        ]


class EntryLog(BaseModel):
    student = models.ForeignKey("exam.Student", on_delete=models.CASCADE, related_name='entries')
    first_image = models.TextField(blank=True, null=True)
    last_image = models.TextField(blank=True, null=True)
    accuracy = models.PositiveSmallIntegerField(default=0)
    max_accuracy = models.PositiveSmallIntegerField(default=0)
    first_enter_time = models.DateTimeField(blank=True, null=True)
    last_enter_time = models.DateTimeField(blank=True, null=True)
    is_hand_checking = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student}"


    class Meta:
        verbose_name = 'EntryLog'
        verbose_name_plural = 'EntryLogs'
        db_table = 'entry_log'