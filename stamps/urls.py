from django.urls import path

from stamps.views.stamp import StampCreateView, StampListView
from stamps.views.expected_stamp import ExpectedStampListView, ExpectedStampCreateView

urlpatterns = [
    path("", StampListView.as_view(), name="stamp_list"),
    path("add/", StampCreateView.as_view(), name="add_stamp"),
    path(
        "expected_stamps/", ExpectedStampListView.as_view(), name="expected_stamp_list"
    ),
    path("add_expected_stamp/",ExpectedStampCreateView.as_view() , name="add_expected_stamp"),
]
