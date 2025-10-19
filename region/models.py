from django.db import models
from core.models.base import BaseModel
from auditlog.registry import auditlog

class Region(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    number = models.IntegerField(default=0, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'
        db_table = 'region'


class Zone(BaseModel):
    region = models.ForeignKey("region.Region", on_delete=models.SET_NULL, null=True, help_text='hudud')
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Bino'
        verbose_name_plural = 'Binolar'
        db_table = 'zone'


class SwingBarrier(BaseModel):
    zone = models.ForeignKey('region.Zone', on_delete=models.SET_NULL, related_name="zones", null=True, help_text='Bino')
    name = models.CharField(max_length=255)
    model = models.CharField(max_length=255, null=True, blank=True)
    number = models.IntegerField(default=0)
    brand = models.CharField(max_length=255, default="Hikvision")
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=255, unique=True)
    port = models.IntegerField(default='80')
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    status = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.zone.region.name} - {self.mac_address} - {self.ip_address}"

    class Meta:
        verbose_name = 'Turniket'
        verbose_name_plural = 'Turniketlar'
        db_table = 'swing_barrier'


class MonitorPc(BaseModel):
    sb = models.ForeignKey('region.SwingBarrier', on_delete=models.SET_NULL, null=True, help_text='Turniket')
    name = models.CharField(max_length=255)
    number = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=255, unique=True)
    status = models.BooleanField(default=False)


    def __str__(self):
        return self.mac_address

    class Meta:
        verbose_name = 'MonitorPc'
        verbose_name_plural = 'Monitorlar'
        db_table = 'monitor_pc'


auditlog.register(Region)
auditlog.register(Zone)
auditlog.register(SwingBarrier)
auditlog.register(MonitorPc)