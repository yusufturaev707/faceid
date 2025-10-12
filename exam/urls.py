from django.urls import path, include
from rest_framework import routers

from exam.views import ExamViewSet, StudentListView

router = routers.DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exams')
urlpatterns = [
    path('', include(router.urls)),
    path('students/', StudentListView.as_view(), name='student-list'),
]