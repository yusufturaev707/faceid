import time
from django.contrib import admin, messages
from exam.models import Student
from face.models import GenerateFaceExam
from face.services import main_worker
from region.models import Region


@admin.action(description="Generation Face")
def generate_face_encode(self, request, queryset):
    try:
        if queryset.count() > 1:
            self.message_user(request, "Siz bitta obyektni tanlay olasiz!", level=messages.WARNING)
            return
        queryset_object = queryset.first()

        test_dates = ['23.09.2025', '24.09.2025']
        region_list = [r for r in Region.objects.all().order_by('number')]
        for test_date in test_dates:
            for region in region_list:
                student_queryset = list(Student.objects.filter(
                    exam=queryset_object.exam, test_day=test_date.strip(), region=region).only('id', 'embedding', 'is_face', 'is_image', 'img_b64'))
                if len(student_queryset) == 0:
                    continue
                try:
                    print(f"COUNT {len(student_queryset)}")
                    main_worker(student_queryset)
                    self.message_user(request, f"Processed {student_queryset.count} students", level=messages.SUCCESS)
                except Exception as e:
                    print(f"async_to_sync error: {e}")
                time.sleep(5)
        # is_null_count = Student.objects.filter(exam=queryset_object, embedding__isnull=True).count()
        # if is_null_count == 0:
        #     # queryset_object.status = SessionStatus.GENERATE
        #     # queryset_object.save()
        #     self.message_user(request, "Muvaffaqiyatli generatsiya bo'ldi!", level=messages.SUCCESS)
        # elif is_null_count > 0:
        #     self.message_user(request, f"{is_null_count} ta ma'lumot saqlanmadi!", level=messages.WARNING)
    except Exception as e:
        print(f"Error: {e}")
        self.message_user(request, str(e), level=messages.ERROR)

@admin.register(GenerateFaceExam)
class GenerateFaceExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'exam__start_date', 'exam__finish_date', 'exam__sm_count', 'exam__total_taker', 'exam__is_finished', 'exam__status',)
    list_per_page = 50

    actions = [generate_face_encode]
