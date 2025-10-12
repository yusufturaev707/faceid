from rest_framework import serializers

from region.serializers import ZoneSerializer
from users.models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'code']


class UserSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'zone']