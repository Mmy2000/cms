from django.contrib import admin
from django.urls import path, include, re_path
from site_settings.views import custom_404_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('content.urls')),
    path('stamps/', include('stamps.urls')),
    path('accounts/', include('accounts.urls')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns.append(re_path(r'^.*$', custom_404_view))  # Placeholder for custom 404 view
