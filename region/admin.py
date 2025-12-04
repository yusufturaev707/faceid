from django.contrib import admin, messages
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy, path
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from unfold.contrib.filters.admin import (RangeDateFilter, RangeDateTimeFilter, )
from unfold.decorators import action
from unfold.enums import ActionVariant
from django.utils.translation import gettext_lazy as _


from region.models import Region, Zone, SwingBarrier
from region.utils import is_check_healthy, delete_all_visitors_clean, get_all_visitors
from users.models import User


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ['id', 'name', 'number', 's_number', 'status']
    list_display_links = ['id', 'name']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['name', 'number',]



@admin.register(Zone)
class ZoneAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    # export_form_class = ExportForm
    export_form_class = SelectableFieldsExportForm

    list_filter_submit = True

    list_display = ['id', 'name', 'number', 'region', 'status']
    list_display_links = ['id', 'name']
    list_filter = (
        'region', 'status',
        ("created_at", RangeDateFilter),
        ("updated_at", RangeDateTimeFilter),
    )
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['region__name', 'name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(region=user_region)
        return qs.none()


@admin.register(SwingBarrier)
class SwingBarrierAdmin(ModelAdmin):
    list_display = ['id', 'ip_address', 'get_region', 'zone', 'number', 'model', 'mac_address', 'person_count', 'status']
    list_display_links = ['id', 'zone', 'ip_address']
    list_filter = ['zone__region__name', 'status', 'brand']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']

    @admin.display(description='Viloyat')
    def get_region(self, obj):
        return obj.zone.region.name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = User.objects.get(id=request.user.id)

        if user.is_admin or user.is_central:
            return qs

        user_region = getattr(request.user, "region", None)
        if user_region:
            return qs.filter(zone__region=user_region)
        return qs.none()

    actions_list = ["check_healthy", "delete_persons_action"]

    @action(description=_("Ish holatini tekshirish"), url_path="check-healthy", permissions=["check_healthy"], icon="check_circle", variant=ActionVariant.INFO)
    def check_healthy(self, request: HttpRequest):
        item_queryset = SwingBarrier.objects.all().order_by('zone__region__number', 'zone__number', 'number')
        total_sb = item_queryset.count()
        active_count = 0
        for item in item_queryset:
            try:
                ip = item.ip_address
                username = item.username
                password = item.password

                if is_check_healthy(ip_address=ip, username=username, password=password):
                    item.status = True
                    active_count += 1
                else:
                    item.status = False
                persons_list = get_all_visitors(ip_address=ip, username=username, password=password)
                item.person_count = len(persons_list)
                item.save()
            except Exception as e:
                self.message_user(request, f"Turniket: {item.zone.region.name}|{item.ip_address} - {e}!", level=messages.ERROR)
                continue
        self.message_user(request, f"Umumiy soni: {total_sb}, Aktiv: {active_count}")
        return redirect(
            reverse_lazy("admin:region_swingbarrier_changelist")
        )

    def has_check_healthy_permission(self, request):
        return request.user.is_admin or request.user.is_central or request.user.is_delegate


    @action(description=_("Tozalash"), url_path="delete-persons-action", permissions=["delete_persons_action"], icon="delete", variant=ActionVariant.DANGER)
    def delete_persons_action(self, request):
        if request.user.is_admin or request.user.is_central:
            item_queryset = SwingBarrier.objects.filter(status=True).order_by('zone__region__number', 'zone__number',
                                                                              'zone__number')
            total_sb = item_queryset.count()
            for item in item_queryset:
                ip = item.ip_address
                username = item.username
                password = item.password

                is_healthy: bool = is_check_healthy(ip_address=ip, username=username, password=password)
                if not is_healthy:
                    item.status = False
                    self.message_user(request,
                                      f"Turniket: {item.zone.region.name}|{item.ip_address} - aloqa mavjud emas!",
                                      level=messages.ERROR)
                    continue
                total, success_count = delete_all_visitors_clean(ip, username, password)
                if total == success_count:
                    item.person_count = 0
                    self.message_user(request,
                                      f"Turniket: {item.zone.region.name}|{item.ip_address} - Total:{total}, Success:{success_count}",
                                      level=messages.SUCCESS)
                elif total != success_count:
                    item.person_count = total - success_count
                    self.message_user(request,
                                      f"Turniket: {item.zone.region.name}|{item.ip_address} - Total:{total}, Success:{success_count}",
                                      level=messages.WARNING)
                item.status = True
                item.save()
            if total_sb == 0:
                self.message_user(request, f"Aktiv turniketlar topilmadi.", level=messages.WARNING)
            else:
                self.message_user(request, f"Jarayon tugadi.", level=messages.INFO)
        else:
            self.message_user(request, f"Sizda ruxsat yo'q.", level=messages.WARNING)
        return redirect(
            reverse_lazy("admin:region_swingbarrier_changelist")
        )

    def has_delete_persons_action_permission(self, request):
        return request.user.is_admin or request.user.is_central