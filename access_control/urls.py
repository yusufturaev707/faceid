from django.urls import path, include
from access_control.views import (
    HikvisionWebhookView, student_access_monitor, TurnstileListView, ActiveExamListView, ZoneListView
)

urlpatterns = [
    path('hikvision/face_event/', HikvisionWebhookView.as_view(), name='hikvision-webhook'),
    path('active-exam-list/', ActiveExamListView.as_view(), name='active-exam-list'),
    path('zone-list/', ZoneListView.as_view(), name='zone-list'),
    path('turnstile-list/', TurnstileListView.as_view(), name='turnstile-list'),
    path('monitor/', student_access_monitor, name='student-monitor'),
]