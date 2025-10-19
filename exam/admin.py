from django.contrib import admin
from unfold.admin import ModelAdmin
from exam.models import Exam, Test, ExamState, Student, Shift, StudentPsData, StudentLog, ExamShift, Reason, Cheating, \
    StudentBlacklist


@admin.register(Test)
class TestAdmin(ModelAdmin):
    list_display = ['id', 'name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    readonly_fields = ['id']
    search_fields = ['name']


@admin.register(Shift)
class ShiftAdmin(ModelAdmin):
    list_display = ['id', 'name', 'number', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number']


@admin.register(ExamShift)
class ExamShiftAdmin(ModelAdmin):
    list_display = ['id', 'exam', 'sm', 'access_time', 'expire_time']
    list_filter = ['exam__test', 'sm']
    readonly_fields = ['id']
    search_fields = ['exam__test__name']


@admin.register(ExamState)
class ExamStatusAdmin(ModelAdmin):
    list_display = ['id', 'name', 'key']
    list_filter = ['name']
    readonly_fields = ['id']
    search_fields = ['name']


@admin.register(Exam)
class ExamAdmin(ModelAdmin):
    list_display = ['id', 'start_date', 'finish_date', 'test', 'total_taker', 'sm_count', 'is_finished', 'status']
    list_filter = ['start_date', 'test__name', 'is_finished', 'status']
    readonly_fields = ['id']
    search_fields = ['start_date', 'test__name', 'is_finished']


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ['id', 'zone', 'last_name', 'first_name', 'middle_name', 'e_date', 'e_date',
                    'sm', 'imei', 'gr_n', 'sp', 'is_face',
                    'is_image', 'is_entered', 'is_blacklist', 'is_cheating'
                    ]
    list_filter = ['is_ready', 'is_image', 'is_entered', 'is_cheating', 'is_blacklist']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['last_name', 'first_name', 'middle_name', 'e_date', 'imei']



@admin.register(StudentPsData)
class StudentPsDataAdmin(ModelAdmin):
    list_display = ['id', 'student', 'ps_ser', 'ps_num', 'phone']
    readonly_fields = ['id']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name', 'phone']


@admin.register(StudentLog)
class StudentLogAdmin(ModelAdmin):
    list_display = ['id', 'student', 'img_face', 'pass_time', 'accuracy', 'door', 'is_hand_checked', 'mac_address', 'ip_address']
    list_filter = ['is_hand_checked']
    readonly_fields = ['id']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name', 'mac_address', 'ip_address']



@admin.register(Reason)
class ReasonAdmin(ModelAdmin):
    list_display = ['id', 'name', 'key', 'status']
    readonly_fields = ['id']
    search_fields = ['name']



@admin.register(Cheating)
class CheatingAdmin(ModelAdmin):
    list_display = ['id', 'student', 'reason', 'user', 'imei', 'pic']
    readonly_fields = ['id']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name']


@admin.register(StudentBlacklist)
class StudentBlacklistAdmin(ModelAdmin):
    list_display = ['id', 'imei', 'description', 'created_at', 'updated_at']
    readonly_fields = ['id']
    search_fields = ['imei']