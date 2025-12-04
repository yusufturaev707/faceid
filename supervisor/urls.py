from django.urls import path, include
from supervisor.views import (SupervisorCreateView, EventSupervisorCreateView,)

urlpatterns = [
    path('create/', SupervisorCreateView.as_view(), name='supervisor-create'),
    path('attach-supervisor/', EventSupervisorCreateView.as_view(), name='attach-supervisor'),
]