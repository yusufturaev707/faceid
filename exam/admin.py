import time

from django.contrib import admin, messages
from django.contrib.postgres.fields import ArrayField
from django.db.models import QuerySet, Count, Q
from django.http import HttpRequest
from django.shortcuts import redirect
from django.db import models
from django.utils.html import format_html

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget, ArrayWidget, UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget
from unfold.decorators import action, display
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from asgiref.sync import async_to_sync
from unfold.paginator import InfinitePaginator

from exam import services
from exam.models import Exam, Test, ExamState, Student, Shift, StudentPsData, StudentLog, ExamShift, Reason, Cheating, StudentBlacklist, ExamZoneSwingBar
from region.models import Zone, SwingBarrier
from region.utils import is_check_healthy, delete_all_visitors_clean, push_data_main_worker, add_user_to_swing_barr, \
    upload_single_user_face_image
from users.models import User

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
    list_display = ['id', 'test', 'display_region', 'display_total_student', 'start_date', 'finish_date', 'is_finished', 'status']

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        user = User.objects.get(id=request.user.id)

        if user.is_delegate:
            if 'status' in list_display:
                list_display.remove('status')
        return list_display

    list_filter = ['start_date', 'test__name', 'is_finished', 'status']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['start_date', 'test__name', 'is_finished']
    list_display_links = ['id', 'test']
    list_per_page = 30

    actions = ["load_data_cefr_action", "choose_swing_barrier_action", "push_swing_barrier_action"]
    inlines = [ExamShiftInline]

    fieldsets = (
        ('Test', {
            'fields': ('test', 'start_date', 'finish_date',)
        }),
        ('Holat', {
            'fields': ('status', 'is_finished', )
        }),
        ('Soni', {
            'fields': ('total_taker',)
        }),
        ('Time', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     user = request.user
    #
    #     # Related ma'lumotlarni oldindan yuklash
    #     qs = qs.select_related('zone', 'zone__region')
    #
    #     # Student countni annotate qilish
    #     if user.is_delegate:
    #         qs = qs.annotate(
    #             total_students=Count(
    #                 'student',
    #                 filter=Q(student__zone__region=user.region),
    #                 distinct=True
    #             )
    #         )
    #     else:
    #         qs = qs.annotate(
    #             total_students=Count('student', distinct=True)
    #         )
    #     return qs

    @display(description=_("Umumiy soni"))
    def display_total_student(self, instance: Exam):
        user = User.objects.get(id=self.request.user.id)
        qs = Student.objects.filter(exam=instance)
        if user.is_delegate:
            qs = Student.objects.filter(exam=instance, zone__region=user.region)
        return qs.count()

    @display(description=_("Viloyat"))
    def display_region(self, instance: Exam):
        user = User.objects.get(id=self.request.user.id)
        region = "All"
        if user.is_delegate:
            region = user.region.name
        return f"{region}"

    @action(description=format_html('🟢 Cefr yuklab olish'))
    def load_data_cefr_action(self, request: HttpRequest, queryset: QuerySet):
        try:
            exam_object = queryset.first()
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
        user = User.objects.get(id=request.user.id)
        return user.is_superuser or user.is_central or user.is_admin

    @action(description=format_html("🔵 Testga turniketlarni tayyorlash"))
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
                    self.message_user(request, f"Turniket: {sb.zone.region.name}|{sb.ip_address} - aloqa mavjud emas!",
                                      level=messages.ERROR)
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
        user = User.objects.get(id=request.user.id)
        return user.is_admin or user.is_central

    @action(description=format_html("💎 Turniketlarga talabgorlar ma'lumotini yuklash"))
    def push_swing_barrier_action(self, request: HttpRequest, queryset):
        for exam in queryset:
            sb_queryset = ExamZoneSwingBar.objects.filter(exam=exam, sb__status=True).order_by('sb__zone__region__number', 'sb__zone__number')
            if sb_queryset.count() == 0:
                self.message_user(request, f"Turniket topilmadi!")
                return redirect("admin:exam_exam_changelist")
            # todo
            success_count_user, success_count_img, error_count_user, error_count_img = push_data_main_worker(sb_queryset)
            self.message_user(request, f"Success_user: {success_count_user} | Success_image: {success_count_img} | Error_user: {error_count_user} | Error_img: {error_count_img}")

    @staticmethod
    def has_push_swing_barrier_action_permission(request: HttpRequest):
        user = User.objects.get(id=request.user.id)
        return user.is_admin or user.is_central

    def save_model(self, request, obj, form, change):
        if not change:
            obj.status = ExamState.objects.get(key='new')
        super().save_model(request, obj, form, change)
        return


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
    list_display_links = ['id', 'last_name', 'first_name', 'middle_name', 'imei', 's_code', 'zone']
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(zone__region=user_region)
        return qs.none()



@admin.register(StudentLog)
class StudentLogAdmin(ModelAdmin):
    list_display = ['id', 'mac_address', 'ip_address', 'direction', 'student', 'pass_time', 'status']
    list_filter = ['is_hand_checked', 'direction', 'status']
    readonly_fields = ['id', 'image_tag', 'created_at', 'updated_at', 'student']
    search_fields = ['student__imei', 'student__last_name', 'student__first_name', 'mac_address', 'ip_address']
    list_display_links = ['id', 'mac_address']
    can_delete = False

    fieldsets = (
        (None, {
            'fields': ('student',)
        }),
        ('Turniket', {
            'fields': ('mac_address', 'ip_address', 'direction', 'status', 'pass_time',)
        }),
        ('Time', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Rasm', {
            'fields': ('image_tag',)
        }),
    )


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
        },
        models.TimeField: {
            "widget": UnfoldAdminTextInputWidget(attrs={"type": "time"}),
        },
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(student__zone__region=user_region)
        return qs.none()


@admin.register(ExamZoneSwingBar)
class ExamZoneSwingBarAdmin(ModelAdmin):
    list_display = ['id', 'exam', 'sb', 'real_count', 'pushed_user_count', 'pushed_image_count', 'err_user_count', 'err_image_count', 'status']
    list_filter = ['status', 'sb']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['sb__zone', 'sb__mac_address', 'sb__ip_address']
    list_display_links = ['id', 'exam']

    actions_detail = ["re_upload_image_action"]

    compressed_fields = True
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True
    paginator = InfinitePaginator
    show_full_result_count = True

    formfield_overrides = {
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

    fieldsets = (
        ('Test', {
            'fields': ('exam', )
        }),
        ('Turniket', {
            'fields': ('sb',)
        }),
        ('Umumiy soni', {
            'fields': ('real_count',)
        }),
        ('Warning', {
            'fields': ('pushed_user_count', 'err_user_count', 'pushed_image_count', 'err_image_count',)
        }),
        ('Yuklanmay qolganlar', {
            'fields': ('unpushed_users_imei', 'unpushed_images_imei', )
        }),
        ('Holat', {
            'fields': ('status',)
        }),
        ('Time', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(sb__zone__region=user_region)
        return qs.none()

    @action(
        description="Qayta yuklash",
        permissions=["re_upload_image_action"],
    )
    def re_upload_image_action(self, request, object_id):
        import ast
        try:
            object_id = int(object_id)
            exam_sb_ob = ExamZoneSwingBar.objects.filter(id=object_id).first()
            unpushed_users_imei = str(exam_sb_ob.unpushed_users_imei)
            unpushed_images_imei = str(exam_sb_ob.unpushed_images_imei)
            try:
                unpushed_users_imei_list = ast.literal_eval(unpushed_users_imei)
                unpushed_images_imei_list = ast.literal_eval(unpushed_images_imei)
                parts_day_queryset = ExamShift.objects.filter(exam=exam_sb_ob.exam).order_by('id')
                qs = Student.objects.filter(exam=exam_sb_ob.exam, e_date__gte=exam_sb_ob.exam.start_date, e_date__lte=exam_sb_ob.exam.finish_date)

                pushed_user_count = 0
                un_pushed_user_count = 0
                pushed_img_count = 0
                un_pushed_img_count = 0

                if len(unpushed_users_imei_list) > 0:
                    for item in qs.filter(imei__in=unpushed_users_imei_list).order_by('id'):
                        sm: int = int(item.sm)
                        sm_obj = parts_day_queryset.filter(sm=sm).first()
                        is_added = add_user_to_swing_barr(exam_sb_ob.sb.ip_address, exam_sb_ob.sb.username,
                                                          exam_sb_ob.sb.password, item, sm_obj)
                        if is_added:
                            unpushed_users_imei_list.remove(item.imei)
                            pushed_user_count += 1
                        else:
                            un_pushed_user_count += 1
                        time.sleep(1)
                    exam_sb_ob.unpushed_users_imei = unpushed_users_imei_list
                    exam_sb_ob.pushed_user_count = pushed_img_count
                    exam_sb_ob.err_image_count = un_pushed_img_count
                    exam_sb_ob.save()

                if len(unpushed_images_imei_list) > 0:
                    for item in qs.filter(imei__in=unpushed_images_imei_list).order_by('id'):
                        img_data = {"fpid": item.imei, "img64": item.ps_data.img_b64}
                        is_image_uploaded = upload_single_user_face_image(user_data=img_data, ip_address=exam_sb_ob.sb.ip_address, username=exam_sb_ob.sb.username, password=exam_sb_ob.sb.password)
                        if is_image_uploaded:
                            unpushed_images_imei_list.remove(item.imei)
                            pushed_img_count += 1
                        else:
                            un_pushed_img_count += 1
                        time.sleep(1)
                    exam_sb_ob.unpushed_images_imei = unpushed_images_imei_list
                    exam_sb_ob.pushed_image_count = pushed_img_count
                    exam_sb_ob.err_image_count = un_pushed_img_count
                    exam_sb_ob.save()

            except ValueError as e:
                print(f"Xatolik: Listni konvertatsiya qilishda xato yuz berdi. String formati noto'g'ri: {e}")
        except Exception as e:
            messages.error(request, str(e))
        finally:
            return redirect(request.headers["referer"])

    def has_re_upload_image_action_permission(self, request, object_id):
        return request.user.is_admin or request.user.is_central


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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(student__zone__region=user_region)
        return qs.none()


@admin.register(StudentBlacklist)
class StudentBlacklistAdmin(ModelAdmin):
    list_display = ['id', 'imei', 'description', 'created_at', 'updated_at']
    readonly_fields = ['id']
    search_fields = ['imei']
    list_display_links = ['id', 'imei']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(student__zone__region=user_region)
        return qs.none()