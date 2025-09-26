from django.contrib import admin
from exam.models import Exam, Test, Status, Student


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    readonly_fields = ['id']
    search_fields = ['name']


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'key', 'created_at', 'updated_at']
    list_filter = ['name']
    readonly_fields = ['id']
    search_fields = ['name']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['id', 'start_date', 'finish_date', 'test', 'total_taker', 'sm_count', 'is_finished', 'status']
    list_filter = ['start_date', 'test__name', 'is_finished', 'status']
    readonly_fields = ['id']
    search_fields = ['start_date', 'test__name', 'is_finished']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'region', 'last_name', 'first_name', 'middle_name', 'test_day', 'e_date', 'e_time',
                    'sm', 'imei', 'group', 'seat', 'is_active', 'is_face',
                    'is_image', 'is_entered', 'subject_id', 'subject_name', 'lang_id', 'level_id', 'phone',
                    'ps_ser', 'ps_number'
                    ]
    list_filter = ['region', 'test_day', 'is_active', 'is_image', 'is_entered']
    readonly_fields = ['id']
    search_fields = ['last_name', 'first_name', 'middle_name', 'test_day', 'e_date', 'imei',  'phone', 'ps_ser', 'ps_number']