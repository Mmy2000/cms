from django.contrib import admin
from django.urls import path, include, re_path
from site_settings.views import custom_404_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('content.urls')),
    path('stamps', include('stamps.urls')),
    # path('summernote/', include('django_summernote.urls')),
]

urlpatterns.append(re_path(r'^.*$', custom_404_view))  # Placeholder for custom 404 view