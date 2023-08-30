# import notifications.urls
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profile/', include('director.urls')),
    path('', include('inspector.urls')),
    path('auth/', include('authentication.urls')),
    # path('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)