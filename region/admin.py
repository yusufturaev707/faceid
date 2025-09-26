from django.contrib import admin

from region.models import Region, Zone, IPCameraType, IPCamera, Computer


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'is_part', 'parent_id', 'created_at', 'updated_at']
    list_filter = ['is_part', 'parent_id']
    readonly_fields = ['id']
    search_fields = ['name', 'number',]



@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'number', 'region', 'created_at', 'updated_at']
    list_filter = ['region']
    readonly_fields = ['id']
    search_fields = ['region__name', 'number',]



@admin.register(IPCameraType)
class IPCameraTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'created_at', 'updated_at']
    readonly_fields = ['id']
    search_fields = ['name', 'code',]


@admin.register(IPCamera)
class IPCameraAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'name', 'number', 'cam_type', 'ip_address', 'mac_address', 'port', 'status']
    list_filter = ['zone__region__name', 'cam_type', 'brand', 'status']
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'username']



@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ['id', 'zone__region__name', 'zone', 'ip_camera', 'name', 'number', 'ip_address', 'mac_address', 'username', 'password']
    list_filter = ['zone__region__name',]
    readonly_fields = ['id']
    search_fields = ['name', 'number', 'ip_address', 'mac_address', 'username']