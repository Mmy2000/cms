from django.urls import path
from . import views

urlpatterns = [
    path("", views.stamp_list, name="stamp_list"),
    path("add/", views.add_stamp, name="add_stamp"),
]