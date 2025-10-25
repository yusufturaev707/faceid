from django.db import models
from core.models.base import BaseModel
from auditlog.registry import auditlog
from django.utils.translation import gettext_lazy as _

class Region(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Nomi"))
    number = models.IntegerField(default=0, unique=True, verbose_name=_("Dtm nomer"))
    s_number = models.IntegerField(default=0, verbose_name=_("S nomer"))
    status = models.BooleanField(default=True, verbose_name=_("Holat"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'
        db_table = 'region'


class Zone(BaseModel):
    region = models.ForeignKey("region.Region", verbose_name=_("Viloyat"), on_delete=models.SET_NULL, null=True, help_text='hudud')
    name = models.CharField(max_length=255, verbose_name=_("Nom"))
    number = models.IntegerField(default=0, verbose_name=_("Nomer"))
    status = models.BooleanField(default=True, verbose_name=_("Holat"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Bino'
        verbose_name_plural = 'Binolar'
        db_table = 'zone'


class SwingBarrier(BaseModel):
    zone = models.ForeignKey('region.Zone', verbose_name=_("Bino"), on_delete=models.SET_NULL, related_name="zones", null=True, help_text='Bino')
    name = models.CharField(max_length=255, verbose_name=_("Nom"))
    model = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Model"))
    number = models.IntegerField(default=0, verbose_name=_("Nomer"))
    brand = models.CharField(max_length=255, default="Hikvision", verbose_name=_("Brand"))
    serial_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Serial"))
    ip_address = models.GenericIPAddressField(verbose_name=_("IP address"))
    mac_address = models.CharField(max_length=255, unique=True, verbose_name=_("MAC address"))
    port = models.IntegerField(default='80', verbose_name=_("Port"))
    username = models.CharField(max_length=255, verbose_name=_("Login"))
    password = models.CharField(max_length=255, verbose_name=_("Parol"))
    status = models.BooleanField(default=True, verbose_name=_("Holat"))


    def __str__(self):
        return f"{self.zone.region.name} - {self.mac_address} - {self.ip_address}"

    class Meta:
        verbose_name = 'Turniket'
        verbose_name_plural = 'Turniketlar'
        db_table = 'swing_barrier'


class MonitorPc(BaseModel):
    sb = models.ForeignKey('region.SwingBarrier', verbose_name=_("Turniket"), on_delete=models.SET_NULL, null=True, help_text='Turniket')
    name = models.CharField(max_length=255, verbose_name=_("Nom"))
    number = models.IntegerField(default=0, verbose_name=_("Nomer"))
    ip_address = models.GenericIPAddressField(verbose_name=_("IP address"))
    mac_address = models.CharField(max_length=255, unique=True, verbose_name=_("MAC address"))
    status = models.BooleanField(default=False, verbose_name=_("Holat"))


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