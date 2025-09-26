from django.db import models
from core.models.base import BaseModel


class Region(BaseModel):
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0, unique=True)
    is_part = models.BooleanField(default=False)
    parent_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
        db_table = 'region'


class Zone(BaseModel):
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0)
    region = models.ForeignKey("region.Region", on_delete=models.SET_NULL, related_name="zones", null=True, help_text='hudud')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Bino'
        verbose_name_plural = 'Binolar'
        db_table = 'zone'


class IPCameraType(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.IntegerField(default=0, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'IP Camera Turi'
        verbose_name_plural = 'IP Camera Turlari'
        db_table = 'ipcameratype'


class StatusIpCamera(models.TextChoices):
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"
    ERROR = "error", "Error"


class IPCamera(BaseModel):
    zone = models.ForeignKey('region.Zone', on_delete=models.SET_NULL, related_name="cameras", null=True, help_text='Bino')
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0)
    cam_type = models.ForeignKey("region.IPCameraType", on_delete=models.SET_NULL, related_name="cameras", null=True, help_text='ip kamera turi')
    brand = models.CharField(max_length=255, blank=True, null=True)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=255, unique=True, blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    gateway = models.GenericIPAddressField(blank=True, null=True)
    dns_servers = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    rtsp_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, choices=StatusIpCamera.choices, default=StatusIpCamera.OFFLINE)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'IP Camera'
        verbose_name_plural = 'IP Cameralar'
        db_table = 'ipcamera'



class Computer(BaseModel):
    ip_camera = models.ForeignKey('region.IPCamera', on_delete=models.SET_NULL, related_name="computer_cameras", null=True, help_text='Camera')
    region_number = models.IntegerField(default=0)
    zone = models.ForeignKey('region.Zone', on_delete=models.SET_NULL, related_name="computer_zones", null=True, help_text='Bino')
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=255, unique=True, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Computer'
        verbose_name_plural = 'Computers'
        db_table = 'computer'