from rest_framework import serializers

from region.models import Region, Zone, SwingBarrier


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'number', 's_number']



class ZoneSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    class Meta:
        model = Zone
        fields = ['id', 'name', 'number', 'region']



class SwingBarrierSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)
    class Meta:
        model = SwingBarrier
        fields = ['id', 'zone', 'name', 'model', 'number', 'brand', 'serial_number', 'ip_address', 'mac_address', 'port', 'status']