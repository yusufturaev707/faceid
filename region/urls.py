from django.urls import path, include
from rest_framework import routers

from region.views import RegionViewSet

router = routers.DefaultRouter()
router.register(r'regions', RegionViewSet, basename='exams')
urlpatterns = [
    path('', include(router.urls)),
]