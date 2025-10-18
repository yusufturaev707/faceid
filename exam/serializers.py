from rest_framework import serializers
from exam.models import Test, ExamState, Exam, Student, StudentLog


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'name', 'code', 'is_active']


class ExamStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamState
        fields = ['id', 'name', 'key']


class ExamSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)
    status = ExamStateSerializer(read_only=True)

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
        fields = ['id', 'zone', 'last_name', 'first_name', 'middle_name', 'e_date', 'e_date',
                    'sm', 'imei', 'gr_n', 'sp', 'is_face',
                    'is_image', 'is_entered', 'is_blacklist', 'is_cheating'
                  ]


class StudentLogSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())

    class Meta:
        model = StudentLog
        fields = ['student', 'img_face', 'pass_time', 'accuracy', 'door',
                  'ip_address', 'mac_address']
