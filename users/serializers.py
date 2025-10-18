from rest_framework import serializers

from region.serializers import RegionSerializer
from users.models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'code']


class UserSerializer(serializers.ModelSerializer):
    zone = RegionSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'region', 'role']