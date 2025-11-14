from django.urls import path, include
from access_control.views import (
    HikvisionWebhookView, student_access_monitor, TurnstileListView, RegionListView, BuildingListView
)

urlpatterns = [
    path('hikvision/face_event/', HikvisionWebhookView.as_view(), name='hikvision-webhook'),
    path('regions/', RegionListView.as_view(), name='region-list'),
    path('buildings/', BuildingListView.as_view(), name='building-list'),
    path('turnstiles/', TurnstileListView.as_view(), name='turnstile-list'),
    path('monitor/', student_access_monitor, name='student-monitor'),
]