from django.urls import re_path

from access_control import consumers

websocket_urlpatterns = [
    re_path(r'ws/student-access/$', consumers.StudentAccessConsumer.as_asgi()),
]