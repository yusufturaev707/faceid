from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from region.models import Region, Zone, SwingBarrier, MonitorPc


class RegionLogEntryAdmin(LogEntryAdmin):
    list_display = ['created', 'resource_url', 'action', 'actor', 'msg_short']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['object_repr', 'changes', 'actor__username']

# Eski LogEntry admin ni o'chirish va yangisini qo'shish
admin.site.unregister(LogEntry)
admin.site.register(LogEntry, RegionLogEntryAdmin)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number',]



@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'region', 'status']
    list_filter = ['region', 'status']
    readonly_fields = ['id']
    search_fields = ['region__name', 'name']


@admin.register(SwingBarrier)
class SwingBarrierAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'name', 'number', 'model', 'mac_address', 'ip_address', 'port', 'status']
    list_filter = ['zone__region__name', 'status', 'brand']
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']



@admin.register(MonitorPc)
class MonitorPcAdmin(admin.ModelAdmin):
    list_display = ['id', 'sb', 'name', 'number', 'ip_address', 'mac_address', 'status']
    list_filter = ['status']
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'ip_address', 'mac_address']