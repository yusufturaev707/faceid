from django.db import models
from pgvector.django import VectorField
from auditlog.registry import auditlog
from core.models.base import BaseModel
from region.models import Zone


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
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Smena'
        verbose_name_plural = 'Smenalar'
        db_table = 'shift'


class ExamShift(BaseModel):
    exam = models.ForeignKey('exam.Exam', on_delete=models.CASCADE, related_name='exams')
    sm = models.ForeignKey('exam.Shift', on_delete=models.CASCADE, related_name='shifts')
    access_time = models.TimeField()
    expire_time = models.TimeField()

    def __str__(self):
        return f"{self.exam.test.name} - {self.exam.start_date} - {self.sm.name}"

    class Meta:
        verbose_name = 'Test Smena'
        verbose_name_plural = 'Test Smenalar'
        db_table = 'exam_sm'


class ExamState(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    key = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return f"Status: {self.name}"

    class Meta:
        verbose_name = 'Exam holati'
        verbose_name_plural = 'Exam holatlari'
        db_table = 'exam_state'


class Exam(BaseModel):
    test = models.ForeignKey('exam.Test', on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateField()
    finish_date = models.DateField()
    sm_count = models.IntegerField(default=0)
    total_taker = models.IntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    status = models.ForeignKey('exam.ExamState', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.test.name}"

    class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        db_table = 'exam'


class Student(BaseModel):
    exam = models.ForeignKey("exam.Exam", on_delete=models.SET_NULL, blank=True, null=True)
    zone = models.ForeignKey("region.Zone", on_delete=models.SET_NULL, blank=True, null=True)
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
        verbose_name_plural = 'Studentlar'
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
        verbose_name = 'Pasport malumot'
        verbose_name_plural = 'Pasport malumotlari'
        db_table = 'student_ps_data'


class StudentLog(BaseModel):
    student = models.ForeignKey("exam.Student", on_delete=models.SET_NULL, related_name='student_logs', blank=True, null=True)
    img_face = models.TextField(blank=True, null=True)
    door = models.PositiveSmallIntegerField(default=0)
    accuracy = models.PositiveSmallIntegerField(default=0)
    pass_time = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField()
    is_hand_checked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.fio}"

    class Meta:
        verbose_name = 'Student Log'
        verbose_name_plural = 'Student Loglari'
        db_table = 'student_log'


class Reason(BaseModel):
    name = models.CharField(max_length=255)
    key = models.PositiveSmallIntegerField(default=0)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Chetlatish sababi'
        verbose_name_plural = 'Chetlatish sabablari'
        db_table = 'reason'


class Cheating(BaseModel):
    student = models.ForeignKey("exam.Student", on_delete=models.SET_NULL, blank=True, null=True, help_text="Student")
    reason = models.ForeignKey('exam.Reason', on_delete=models.SET_NULL, blank=True, null=True, help_text="Chetlatish sababi")
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, blank=True, null=True, help_text="Chetlatgan vakil")
    imei = models.CharField(max_length=14, db_index=True)
    pic = models.ImageField(upload_to='cheating/', blank=True, null=True)

    def __str__(self):
        return f"{self.imei}"

    class Meta:
        verbose_name = "Chetlatilgan student"
        verbose_name_plural = "Chetlatilgan studentlar"
        db_table = 'cheating'



class StudentBlacklist(BaseModel):
    imei = models.CharField(max_length=14, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.imei}"


    class Meta:
        verbose_name = "Qora ro'yxat"
        verbose_name_plural = "Qora ro'yxatdagilar"
        db_table = 'student_blacklist'


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