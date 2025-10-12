from rest_framework import serializers

from region.models import Region, Zone, IPCameraType, IPCamera


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'number', 'is_part', 'parent_id']



class ZoneSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    class Meta:
        model = Zone
        fields = ['id', 'name', 'number', 'region']


class IPCameraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPCameraType
        fields = ['id', 'name', 'code']


class IPCameraSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)
    cam_type = IPCameraTypeSerializer(read_only=True)
    class Meta:
        model = IPCamera
        fields = ['id', 'zone', 'name', 'number', 'cam_type', 'ip_address', 'mac_address', 'port', 'username', 'password', 'rtsp_url', 'status']


class ComputerSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)
    ip_camera = IPCameraSerializer(read_only=True)
    region_number = RegionSerializer(read_only=True)
    class Meta:
        model = IPCamera
        fields = ['id', 'ip_camera', 'region_number', 'zone', 'name', 'number', 'ip_address', 'mac_address', 'username', 'password']