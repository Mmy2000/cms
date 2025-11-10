# cms/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_topics, name="main_topics"),
    path("<slug:slug>/", views.content_detail, name="content_detail"),
]
