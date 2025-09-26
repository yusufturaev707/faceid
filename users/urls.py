from django.urls import path, include
from rest_framework import routers
from users.views import (LoginView, LogoutView, CustomTokenRefreshView, )

router = routers.DefaultRouter()

# router.register(r'regions', RegionViewSet, basename='regions')
# router.register(r'users', UserViewSet, basename='users')
# router.register(r'student', StudentViewSet, basename='student')
# router.register(r'exam_session', ExamSessionViewSet, basename='exam_session')
# router.register(r'attendance', AttendanceViewSet, basename='attendance')
# router.register(r'reports', ReportViewSet, basename='reports')
# router.register(r'settings_data', SettingDataViewSet, basename='settings_data')

urlpatterns = [
    # path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
]