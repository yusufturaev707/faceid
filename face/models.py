from django.db import models
from django.utils.html import format_html
from core.models.base import BaseModel
from auditlog.registry import auditlog
from exam.models import Exam


class GenerateFaceExam(BaseModel):
    exam = models.ForeignKey('exam.Exam', on_delete=models.SET_NULL, null=True)
    is_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.exam.test.name}: {self.exam.start_date}"



class FaceIdentification(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    token = models.TextField()
    score = models.PositiveSmallIntegerField(default=0)
    verified = models.BooleanField(default=False)
    first_image = models.TextField(blank=True, null=True)
    second_image = models.TextField(blank=True, null=True)
    response_json = models.TextField()
    status = models.PositiveSmallIntegerField(default=0)
    response_time = models.FloatField(default=0)

    def ps_image(self):
        if self.first_image and self.verified is False:
            return format_html(
                '<img src="{}" style="max-width:150px; max-height:150px;" />',
                self.first_image
            )
        return "(No Image)"

    ps_image.short_description = 'Pasport'

    def live_image(self):
        if self.second_image and self.verified is False:
            return format_html(
                '<img src="{}" style="max-width:150px; max-height:150px;" />',
                self.second_image
            )
        return "(No Image)"

    live_image.short_description = 'Camera'

    def __str__(self):
        return f"{self.user.username}"


auditlog.register(FaceIdentification)
auditlog.register(GenerateFaceExam)