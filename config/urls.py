from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

urlpatterns += [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/face/', include('face.urls')),
    path('api/v1/exam/', include('exam.urls')),
    path('api/v1/region/', include('region.urls')),
    path('api/v1/access_control/', include('access_control.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Agar STATICFILES_DIRS ishlatayotgan bo'lsangiz:
    from django.contrib.staticfiles.views import serve
    urlpatterns += [
        path('static/<path:path>', serve),
    ]