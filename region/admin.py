from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from unfold.contrib.filters.admin import (RangeDateFilter, RangeDateTimeFilter, )
from region.models import Region, Zone, SwingBarrier, MonitorPc


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


@admin.register(SwingBarrier)
class SwingBarrierAdmin(ModelAdmin):
    list_display = ['id', 'ip_address', 'get_region', 'zone', 'number', 'model', 'mac_address', 'status']
    list_display_links = ['id', 'zone', 'ip_address']
    list_filter = ['zone__region__name', 'status', 'brand']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']

    @admin.display(description='Viloyat')
    def get_region(self, obj):
        return obj.zone.region.name


@admin.register(MonitorPc)
class MonitorPcAdmin(ModelAdmin):
    list_display = ['id', 'sb', 'name', 'number', 'ip_address', 'mac_address', 'status']
    list_display_links = ['id', 'name']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['name', 'number', 'ip_address', 'mac_address']