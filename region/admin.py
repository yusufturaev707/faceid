from django.contrib import admin

from region.models import Region, Zone, SwingBarrier, Computer


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'status']
    list_filter = ['status']
    readonly_fields = ['name']
    search_fields = ['name', 'number',]



@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'region', 'status']
    list_filter = ['region', 'status']
    readonly_fields = ['name']
    search_fields = ['region__name', 'name']


@admin.register(SwingBarrier)
class SwingBarrierAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'name', 'number', 'model', 'mac_address', 'ip_address', 'port', 'status']
    list_filter = ['zone__region__name', 'status', 'brand']
    readonly_fields = ['mac_address']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']



@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'name', 'number', 'ip_address', 'mac_address', 'status']
    list_filter = ['zone__region__name', 'status']
    readonly_fields = ['mac_address']
    search_fields = ['name', 'number', 'ip_address', 'mac_address']