from django.contrib import admin
from django.db import models
from django.contrib.postgres.fields import ArrayField

from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget, ArrayWidget, UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget
from unfold.decorators import action, display
from unfold.paginator import InfinitePaginator

from access_control.models import NormalUserLog




@admin.register(NormalUserLog)
class NormalUserLogAdmin(ModelAdmin):
    list_display = ['id', 'normal_user_id', 'last_name', 'first_name', 'middle_name', 'normal_user_type', 'get_region', 'zone', 'employee_no', 'ip_address', 'mac_address', 'direction', 'status', 'pass_time',]
    list_filter = ['door', 'direction', 'status']
    readonly_fields = ['id', 'created_at', 'updated_at', 'image_tag', 'get_region']
    search_fields = ['employee_no', 'ip_address', 'mac_address', 'direction', 'status']
    list_display_links = ['id', 'ip_address', 'mac_address', 'direction', 'status', 'employee_no']
    list_per_page = 50


    compressed_fields = True
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True
    paginator = InfinitePaginator
    show_full_result_count = False

    fieldsets = (
        (None, {
            'fields': ('employee_no', 'normal_user_type', 'last_name', 'first_name', 'middle_name', 'normal_user_id',)
        }),
        ('Hudud', {
            'fields': ('get_region', 'zone',)
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

    @display(description='Bino')
    def get_zone(self, obj):
        return f"{obj.zone.name}" if obj.zone else ''

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