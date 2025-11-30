from django.urls import path
from . import views

urlpatterns = [
    path("", views.stamp_list, name="stamp_list"),
    path("add/", views.add_stamp, name="add_stamp"),
    path("expected_stamps/", views.expected_stamp_list, name="expected_stamp_list"),
    path("add_expected_stamp/", views.add_expected_stamp, name="add_expected_stamp"),
]
