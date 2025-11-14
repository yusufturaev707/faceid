from io import BytesIO

from django.contrib import admin
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django import forms
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
import pandas as pd
from django.contrib import messages
import openpyxl
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget, ArrayWidget, UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget
from unfold.decorators import action, display
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.enums import ActionVariant
from unfold.paginator import InfinitePaginator

from access_control.models import NormalUser, StaffRole, NormalUserLog
from users.models import User


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel fayl',
        help_text='Excel faylni tanlang (.xlsx, .xls)',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )

    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']

        # Fayl turini tekshirish
        if not file.name.endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Faqat Excel fayl yuklash mumkin (.xlsx yoki .xls)')

        # Fayl hajmini tekshirish (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Fayl hajmi 10MB dan kichik bo\'lishi kerak')

        return file


@admin.register(NormalUser)
class NormalUserAdmin(ModelAdmin, ExportActionModelAdmin):
    list_display = ['id', 'region', 'role', 'full_name', 'imei', 'ps_data', 'status']
    list_filter = ['region', 'role', 'is_blacklist', 'status']
    readonly_fields = ['id', 'created_at', 'updated_at', 'image_tag']
    search_fields = ['last_name', 'first_name', 'middle_name', 'phone']
    list_display_links = ['id', 'last_name', 'first_name', 'middle_name', 'image_tag', 'region', 'role', 'ps_ser', 'ps_num', 'phone', 'status']
    list_per_page = 30

    actions_list = ['import_changelist_action']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(region=user_region, role__code='supervisor')
        return qs.none()

    fieldsets = (
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'middle_name', 'phone', 'role', 'region')
        }),
        ('Pasport ma\'lumotlari', {
            'fields': ('ps_ser', 'ps_num', 'imei')
        }),
        ('Turniket ruxsati', {
            'fields': ('access_datetime', 'expired_datetime')
        }),
        ('Holat', {
            'fields': ('is_blacklist', 'status')
        }),
        ('Rasm', {
            'fields': ('image_tag',)
        }),
    )

    @display(description='F.I.O')
    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.middle_name or ''}".strip().upper()

    @display(description='VILOYAT')
    def region(self, obj):
        return f"{obj.name}".capitalize()

    @display(description='PASPORT')
    def ps_data(self, obj):
        return f"{obj.ps_ser} {obj.ps_num}"

    @display(description='TELEFON')
    def phone(self, obj):
        return f"{obj.phone}".strip()

    @display(description='STATUS')
    def status(self, obj):
        return obj.status

    @action(description=_("Shablon"), icon="download",  variant=ActionVariant.PRIMARY)
    def template_changelist_action(self, request):
        messages.success(
            request, _("Shablon yuklab olindi!")
        )
        return redirect(reverse_lazy("admin:person_download_template"))


    @action(description=_("Import"), icon="upload", variant=ActionVariant.PRIMARY,  permissions=["import_changelist_action"],)
    def import_changelist_action(self, request):
        messages.success(
            request, _("Person yuklab olindi!")
        )
        return redirect(reverse_lazy("admin:person_import_excel"))


    def has_import_changelist_action_permission(self, request):
        return request.user.is_superuser

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-excel/", self.admin_site.admin_view(self.import_excel_view),
                 name="access_control_normaluser_import_excel"),
            path('download-template/', self.download_template, name='person_download_template'),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        if request.method == 'POST':
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']

                try:
                    # Excel faylni o'qish
                    df = pd.read_excel(excel_file)

                    success_count = 0
                    error_count = 0
                    errors = []

                    # Har bir qatorni o'qish
                    for index, row in df.iterrows():
                        try:
                            # Ma'lumotlarni olish
                            person_data = {
                                'first_name': str(row.get('Ism', '')).strip(),
                                'last_name': str(row.get('Familiya', '')).strip(),
                                'middle_name': str(row.get('Otasining ismi', '')).strip() if pd.notna(
                                    row.get('Otasining ismi')) else '',
                                'gender': str(row.get('Jinsi', 'M')).strip().upper(),
                                'ps_ser': str(row.get('Pasport seriya', '')).strip(),
                                'ps_num': str(row.get('Pasport raqam', '')).strip(),
                                'imei': str(row.get('PINFL', '')).strip() if pd.notna(row.get('PINFL')) else '',
                                'phone': str(row.get('Telefon', '')).strip(),
                            }

                            # Majburiy maydonlarni tekshirish
                            if not person_data['first_name'] or not person_data['last_name']:
                                errors.append(f"Qator {index + 2}: Ism va Familiya bo'sh bo'lishi mumkin emas")
                                error_count += 1
                                continue

                            # Pasport seriya va raqami orqali mavjudligini tekshirish
                            existing_person = NormalUser.objects.filter(
                                ps_ser=person_data['ps_ser'],
                                ps_num=person_data['ps_num']
                            ).first()

                            if existing_person:
                                # Mavjud bo'lsa, yangilash
                                for key, value in person_data.items():
                                    setattr(existing_person, key, value)
                                existing_person.save()
                            else:
                                # Yangi yaratish
                                NormalUser.objects.create(**person_data)

                            success_count += 1

                        except Exception as e:
                            error_count += 1
                            errors.append(f"Qator {index + 2}: {str(e)}")

                    # Xabar ko'rsatish
                    if success_count > 0:
                        messages.success(request, f"✅ Muvaffaqiyatli yuklandi: {success_count} ta shaxs")

                    if error_count > 0:
                        error_message = f"❌ Xatoliklar: {error_count} ta\n" + "\n".join(errors[:10])
                        if len(errors) > 10:
                            error_message += f"\n... va yana {len(errors) - 10} ta xatolik"
                        messages.error(request, error_message)

                    return redirect('..')

                except Exception as e:
                    messages.error(request, f'Xatolik yuz berdi: {str(e)}')
        else:
            form = ExcelImportForm()

        context = {
            'form': form,
            'title': 'Excel fayldan shaxslarni yuklash',
            'site_header': 'Person Import',
            'has_view_permission': True,
        }
        return render(request, "admin/access_control/normaluser/../templates/admin/import_excel.html", context)


    def download_template(self, request):
        # Excel fayl yaratish
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Person Import"

        # Sarlavhalar
        headers = [
            'Familiya', 'Ism', 'Otasining ismi', 'Jinsi', 'Pasport seriya', 'Pasport raqam', 'PINFL','Telefon'
        ]
        ws.append(headers)

        # Namuna ma'lumot
        sample_data = [
            'Oqboyev', 'Qoraboy', 'Sariq o\'g\'li', 'M', 'AA', '1234567', '12345678901234', '+998901234567'
        ]
        ws.append(sample_data)

        # Sarlavhalarni qalin qilish
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)

        # Ustunlar kengligini sozlash
        column_widths = [15, 15, 20, 15, 8, 15, 15, 18]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

        # Faylni saqlash
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=person_shablon.xlsx'

        return response

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

@admin.register(NormalUserLog)
class NormalUserLogAdmin(ModelAdmin):
    list_display = ['id', 'normal_user__region__name', 'normal_user', 'employee_no', 'pass_time', 'ip_address', 'mac_address', 'direction', 'status']
    list_filter = ['door', 'direction', 'normal_user__region__name', 'status']
    readonly_fields = ['id', 'created_at', 'updated_at', 'image_tag']
    search_fields = ['employee_no', 'normal_user__first_name', 'normal_user__middle_name', 'normal_user__last_name', 'ip_address', 'mac_address', 'direction', 'status']
    list_display_links = ['id', 'normal_user']
    list_per_page = 50


    compressed_fields = True
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True
    paginator = InfinitePaginator
    show_full_result_count = False

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


@admin.register(StaffRole)
class StaffRoleAdmin(ModelAdmin):
    list_display = ['id', 'name', 'code', 'status', 'created_at', 'updated_at']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['name', 'code']
    list_display_links = ['id', 'name']
    list_per_page = 10


    compressed_fields = True
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True
    paginator = InfinitePaginator
    show_full_result_count = False

    formfield_overrides = {
        models.TimeField: {
            "widget": UnfoldAdminTextInputWidget(attrs={"type": "time"}),
        },
    }