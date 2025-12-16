# cms/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.main_topics, name="main_topics"),
    path("<int:id>/", views.content_detail, name="content_detail"),
]

