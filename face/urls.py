from django.urls import path, include
from rest_framework import routers
from face.views import *
from face.views import (StudentViewSet, )

router = routers.DefaultRouter()
router.register(r'faces', StudentViewSet, basename='faces')
urlpatterns = [
    path('', include(router.urls)),
path('auth/login/', LoginView.as_view(), name='login'),
]