import time
from django.contrib import admin, messages
from django.contrib.postgres.fields import ArrayField
from django.http import HttpRequest
from django.shortcuts import redirect
from django.db import models

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget, ArrayWidget, UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget
from unfold.decorators import action
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.enums import ActionVariant

from asgiref.sync import async_to_sync
from unfold.paginator import InfinitePaginator

from exam import services
from exam.models import Exam, Test, ExamState, Student, Shift, StudentPsData, StudentLog, ExamShift, Reason, Cheating, StudentBlacklist, ExamZoneSwingBar
from region.models import Zone, SwingBarrier
from region.utils import is_check_healthy, delete_all_visitors_clean, push_data_main_worker

admin.site.disable_action('delete_selected')


class ExamShiftInline(admin.StackedInline):
    model = ExamShift
    max_num = 4
    extra = 1
    fields = ('exam', 'sm', 'access_time', 'expire_time')

    can_delete = False

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        },
        models.ForeignKey: {
            "widget": UnfoldAdminSelectWidget,
        },
        models.TimeField: {
            "widget": UnfoldAdminTextInputWidget(attrs={"type": "time"}),
        },
    }


@admin.register(Exam)
class ExamAdmin(ModelAdmin):
    list_display = ['id', 'test', 'total_taker', 'start_date', 'finish_date', 'is_finished', 'status']
    list_filter = ['start_date', 'test__name', 'is_finished', 'status']
    readonly_fields = ['id', 'created_at', 'updated_at', 'status']
    search_fields = ['start_date', 'test__name', 'is_finished']
    list_display_links = ['id', 'test']

    actions_row  = ["load_data_cefr_action"]
    actions = ["choose_swing_barrier_action", "push_swing_barrier_action"]
    inlines = [ExamShiftInline]

    @action(
        description=_("Cefr yuklab olish"),
        permissions=["load_data_cefr_action"],
        url_path="load-data-cefr-action",
        # attrs={"target": "_blank"},
        icon="api",
        variant=ActionVariant.SUCCESS,
    )
    def load_data_cefr_action(self, request: HttpRequest, object_id: int):
        try:
            exam_object = Exam.objects.get(id=object_id)
            state_key = exam_object.status.key
            if not state_key == 'new':
                messages.warning(request, f"Ma'lumot yuklab olish holatida emas!")
                return redirect("admin:exam_exam_changelist")
            t = async_to_sync(services.get_all_users_cefr)(exam_object)
            if len(t) == 0:
                messages.error(request, _(f"Ma'lumot yozilmadi."))
                return redirect(
                    reverse_lazy("admin:exam_exam_changelist")
                )
            exam_object.status = ExamState.objects.get(key='load_data')
            exam_object.total_taker = len(t)
            exam_object.save()
            time.sleep(3)
            messages.success(request, _(f"Jarayon yakunlandi."))
            return redirect(
                reverse_lazy("admin:exam_exam_changelist")
            )
        except Exception as e:
            messages.error(request, str(e))
            return redirect("admin:exam_exam_changelist")

    @staticmethod
    def has_load_data_cefr_action_permission(request: HttpRequest):
        user = request.user
        return user.is_superuser or user.is_central or user.is_admin

    @action(
        description=_("Turniketlarga talabgorlar ma'lumotini yuklash"),
        url_path="push-swing-barrier-action",
        permissions=["push_swing_barrier_action"],
        icon="send",
        variant=ActionVariant.PRIMARY,
    )
    def push_swing_barrier_action(self, request: HttpRequest, queryset):
        for exam in queryset:
            sb_queryset = ExamZoneSwingBar.objects.filter(exam=exam, sb__status=True).order_by('sb__zone__region__number', 'sb__zone__number')
            if sb_queryset.count() == 0:
                self.message_user(request, f"Turniket topilmadi!")
                return redirect("admin:exam_exam_changelist")
            success_count_user, success_count_img, error_count_user, error_count_img = push_data_main_worker(sb_queryset)
            self.message_user(request, f"Success_user: {success_count_user} | Success_image: {success_count_img} | Error_user: {error_count_user} | Error_img: {error_count_img}")

    @staticmethod
    def has_push_swing_barrier_action_permission(request: HttpRequest):
        user = request.user
        return user.is_admin or user.is_central


    @action(
        description=_("Testga turniketlarni tayyorlash"),
        url_path="choose-swing-barrier-action",
        permissions=["choose_swing_barrier_action"],
        icon="send",
        variant=ActionVariant.INFO,
    )
    def choose_swing_barrier_action(self, request: HttpRequest, queryset):
        if queryset.count() == 0:
            self.message_user(request, "Tadbir tanlanmadi!", level=messages.ERROR)
            return redirect("admin:exam_exam_changelist")
        if queryset.count() > 1:
            self.message_user(request, "Faqat 1 ta tadbirni tanlang!", level=messages.ERROR)
            return redirect("admin:exam_exam_changelist")
        if queryset.count() == 1:
            sb_queryset = SwingBarrier.objects.filter(status=True, zone__region__status=True,
                                                      zone__status=True).order_by('zone__region__number',
                                                                                  'zone__number')
            if sb_queryset.count() == 0:
                self.message_user(request, "Turniket topilmadi", level=messages.WARNING)
                return redirect("admin:exam_exam_changelist")

            swb_to_create = []

            for sb in sb_queryset:
                ip: str = sb.ip_address
                mac: str = sb.mac_address
                username: str = sb.username
                password: str = sb.password

                is_healthy: bool = is_check_healthy(ip, mac, username, password)
                if not is_healthy:
                    print(f"{sb.ip_address} ishlamayapti!")
                    continue

                is_deleted = delete_all_visitors_clean(ip, username, password)
                if not is_deleted:
                    self.message_user(request, "Xatolik yuz berdi!", level=messages.ERROR)
                self.message_user(request, f"{ip}: muvaffaqiyatli o'chirildi!", level=messages.SUCCESS)

                exam_sb_queryset = ExamZoneSwingBar.objects.filter(exam=queryset.first(), sb=sb).order_by('id')

                if exam_sb_queryset.exists():
                    ex_sb = exam_sb_queryset.first()
                    ex_sb.unpushed_users_imei = ''
                    ex_sb.unpushed_images_imei = ''
                    ex_sb.real_count = 0
                    ex_sb.pushed_user_count = 0
                    ex_sb.pushed_image_count = 0
                    ex_sb.err_user_count = 0
                    ex_sb.err_image_count = 0
                    ex_sb.status = False
                    ex_sb.save()
                    continue
                swb_to_create.append(
                    ExamZoneSwingBar(
                        exam=queryset.first(),
                        sb=sb,
                        status=True
                    )
                )
            ExamZoneSwingBar.objects.bulk_create(swb_to_create, batch_size=50, ignore_conflicts=True)
            return redirect("admin:exam_exam_changelist")

    @staticmethod
    def has_choose_swing_barrier_action_permission(request: HttpRequest):
        user = request.user
        return user.is_admin or user.is_central


    def save_model(self, request, obj, form, change):
        if not change:
            obj.status = ExamState.objects.get(key='new')
        super().save_model(request, obj, form, change)
        return

    class Media:
        js = (
            'https://unpkg.com/htmx.org@1.9.10',
            'unfold/js/htmx_spinner.js',
        )
        css = {
            'all': ('unfold/css/htmx_spinner.css',)
        }


@admin.register(Test)
class TestAdmin(ModelAdmin):
    list_display = ['id', 'name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    readonly_fields = ['id']
    search_fields = ['name']
    list_display_links = ['id', 'name']


@admin.register(Shift)
class ShiftAdmin(ModelAdmin):
    list_display = ['id', 'name', 'number', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number']
    list_display_links = ['id', 'name']


@admin.register(ExamState)
class ExamStatusAdmin(ModelAdmin):
    list_display = ['id', 'name', 'key']
    list_filter = ['name']
    readonly_fields = ['id']
    search_fields = ['name']
    list_display_links = ['id', 'name']


class StudentPsDataInline(admin.StackedInline):
    model = StudentPsData
    max_num = 1
    extra = 0
    fields = ('ps_ser', 'ps_num', 'phone', 'image_tag', 'embedding')
    readonly_fields = ('image_tag', 'embedding')


    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        },
        models.CharField: {
            "widget": UnfoldAdminTextInputWidget,
        },
    }


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ['id', 'last_name', 'first_name', 'middle_name', 'imei', 's_code', 'zone', 'e_date', 'sm', 'gr_n', 'is_entered']
    list_filter = ['is_ready', 'is_image', 'is_entered', 'is_cheating', 'is_blacklist', 'zone__region']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['last_name', 'first_name', 'middle_name', 'e_date', 'imei', 's_code']
    list_display_links = ['id', 'name']
    list_per_page = 20


    compressed_fields = True
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True
    paginator = InfinitePaginator
    show_full_result_count = False

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        }
    }
    inlines = [StudentPsDataInline]



@admin.register(StudentLog)
class StudentLogAdmin(ModelAdmin):
    list_display = ['id', 'mac_address', 'ip_address', 'direction', 'student', 'pass_time', 'status']
    list_filter = ['is_hand_checked', 'direction', 'status']
    readonly_fields = ['id', 'image_tag']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name', 'mac_address', 'ip_address']
    list_display_links = ['id', 'mac_address']


@admin.register(ExamZoneSwingBar)
class ExamZoneSwingBarAdmin(ModelAdmin):
    list_display = ['id', 'exam', 'sb', 'real_count', 'pushed_user_count', 'pushed_image_count', 'err_user_count', 'err_image_count', 'status']
    list_filter = ['status', 'sb__zone__region']
    readonly_fields = ['id']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name', 'mac_address', 'ip_address']
    list_display_links = ['id', 'exam']



@admin.register(Reason)
class ReasonAdmin(ModelAdmin):
    list_display = ['id', 'name', 'key', 'status']
    readonly_fields = ['id']
    search_fields = ['name']
    list_display_links = ['id', 'name']



@admin.register(Cheating)
class CheatingAdmin(ModelAdmin):
    list_display = ['id', 'student', 'reason', 'user', 'imei', 'pic']
    readonly_fields = ['id']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name']
    list_display_links = ['id', 'student']


@admin.register(StudentBlacklist)
class StudentBlacklistAdmin(ModelAdmin):
    list_display = ['id', 'imei', 'description', 'created_at', 'updated_at']
    readonly_fields = ['id']
    search_fields = ['imei']
    list_display_links = ['id', 'imei']