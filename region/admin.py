from django.contrib import admin
from unfold.admin import ModelAdmin
from region.models import Region, Zone, SwingBarrier, MonitorPc


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ['id', 'name', 'number', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number',]



@admin.register(Zone)
class ZoneAdmin(ModelAdmin):
    list_display = ['id', 'name', 'number', 'region', 'status']
    list_filter = ['region', 'status']
    readonly_fields = ['id']
    search_fields = ['region__name', 'name']


@admin.register(SwingBarrier)
class SwingBarrierAdmin(ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'name', 'number', 'model', 'mac_address', 'ip_address', 'port', 'status']
    list_filter = ['zone__region__name', 'status', 'brand']
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']



@admin.register(MonitorPc)
class MonitorPcAdmin(ModelAdmin):
    list_display = ['id', 'sb', 'name', 'number', 'ip_address', 'mac_address', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'ip_address', 'mac_address']