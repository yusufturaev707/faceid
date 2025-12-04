from datetime import datetime

from rest_framework import serializers

from exam.models import Exam
from region.models import Region
from supervisor.models import Supervisor, EventSupervisor


class SupervisorSerializer(serializers.ModelSerializer):
    region_number = serializers.IntegerField(write_only=True)
    class Meta:
        model = Supervisor
        fields = ['id', 'last_name', 'first_name', 'middle_name', 'imei', 'ps_ser', 'ps_num', 'img_b64', 'gender', 'region_number']

    def create(self, validated_data):
        region_num = validated_data.pop('region_number')
        try:
            region = Region.objects.get(number=region_num)
        except Region.DoesNotExist:
            raise serializers.ValidationError({
                'success': False,
                'message': 'Ma\'lumotlar noto\'g\'ri',
                'errors': f"Region with number={region_num} not found."
            })

        validated_data['region'] = region
        return Supervisor.objects.create(**validated_data)


class EventSupervisorSerializer(serializers.ModelSerializer):
    imei = serializers.CharField(write_only=True, max_length=255)
    exam_hash_key = serializers.CharField(write_only=True, max_length=255)
    class Meta:
        model = EventSupervisor
        fields = ['id', 'imei', 'exam_hash_key', 'zone', 'category_key', 'category_name', 'test_date', 'sm', 'group_n']

    def create(self, validated_data):
        exam_hash_key = validated_data.pop('exam_hash_key')
        imei = validated_data.pop('imei')
        test_date = validated_data.pop('test_date')
        sm = validated_data.pop('sm')

        queryset = EventSupervisor.objects.filter(exam__hash_key=exam_hash_key, supervisor__imei=imei, test_date=test_date, sm=sm)
        if queryset.exists():
            raise serializers.ValidationError({
                'success': False,
                'message': 'Ma\'lumotlar noto\'g\'ri',
                'errors': f"Supervisor with imei={imei} {test_date} {sm} uchun yuborilgan!"
            })

        try:
            exam = Exam.objects.get(hash_key=exam_hash_key)
            supervisor = Supervisor.objects.get(imei=imei)
        except Exam.DoesNotExist:
            raise serializers.ValidationError({
                'success': False,
                'message': 'Ma\'lumotlar noto\'g\'ri',
                'errors': f"Exam with number={exam_hash_key} not found."
            })
        except Supervisor.DoesNotExist:
            raise serializers.ValidationError({
                'success': False,
                'message': 'Ma\'lumotlar noto\'g\'ri',
                'errors': f"Supervisor with imei={imei} not found."
            })

        validated_data['exam'] = exam
        validated_data['supervisor'] = supervisor
        #todo
        validated_data['access_datetime'] = datetime.now()
        validated_data['expired_datetime'] = datetime.now()
        return EventSupervisor.objects.create(**validated_data)