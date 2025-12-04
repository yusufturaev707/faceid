from django.urls import path, include
from users.views import (LoginView, LogoutView, CustomTokenRefreshView, )

urlpatterns = [
    # path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
]