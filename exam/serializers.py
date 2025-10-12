from rest_framework import serializers

from exam.models import Test, Status, Exam, Student, EntryLog
from region.models import Region, Zone, IPCameraType, IPCamera
from region.serializers import RegionSerializer, ZoneSerializer


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'name', 'code', 'is_active']


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'name', 'key']


class IPCameraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPCameraType
        fields = ['id', 'name', 'code']


class ExamSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)
    status = StatusSerializer(read_only=True)
    class Meta:
        model = Exam
        fields = ['id', 'start_date', 'finish_date', 'sm_count', 'test', 'total_taker', 'is_finished', 'status']


class StudentSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_number = serializers.CharField(source='zone.number', read_only=True)
    region_name = serializers.CharField(source='zone.region.name', read_only=True)
    exam_id = serializers.CharField(source='exam.id', read_only=True)
    exam_name = serializers.CharField(source='exam.test.name', read_only=True)
    class Meta:
        model = Student
        fields = ['id', 'exam_name', 'exam_id', 'last_name', 'first_name', 'middle_name', 'test_day', 'sm', 'imei', 'group', 'seat', 'subject_id', 'subject_name', 'is_entered', 'is_face', 'is_image', 'is_active', 'zone_number', 'zone_name', 'region_name', 'embedding', 'img_b64']


class EntryLogSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())

    class Meta:
        model = EntryLog
        fields = ['student', 'first_image', 'last_image', 'accuracy', 'max_accuracy', 'first_enter_time', 'last_enter_time', 'is_hand_checking']