from django.urls import path

from stamps.views.stamp import (
    StampCreateView,
    StampListView,
    GroupedStampListView,
    StampDetailView,
    StampDashboardView,
)
from stamps.views.expected_stamp import ExpectedStampListView, ExpectedStampCreateView, GroupedExpectedStampListView,ExpectedStampDetailView,ExpectedStampDashboardView

urlpatterns = [
    path("", StampListView.as_view(), name="stamp_list"),
    path("add/", StampCreateView.as_view(), name="add_stamp"),
    path("grouped_by_company/", GroupedStampListView.as_view(), name="grouped_stamps"),
    path(
        "expected_stamps/", ExpectedStampListView.as_view(), name="expected_stamp_list"
    ),
    path(
        "add_expected_stamp/",
        ExpectedStampCreateView.as_view(),
        name="add_expected_stamp",
    ),
    path(
        "grouped_by_sector/",
        GroupedExpectedStampListView.as_view(),
        name="grouped_expected_stamps",
    ),
    path("<int:stamp_id>/", StampDetailView.as_view(), name="stamp_detail"),
    path(
        "expected_stamps/<int:stamp_id>/",
        ExpectedStampDetailView.as_view(),
        name="expected_stamp_detail",
    ),
    path("stamp_dashboard/", StampDashboardView.as_view(), name="stamp_dashboard"),
    path(
        "expected_stamp_dashboard/",
        ExpectedStampDashboardView.as_view(),
        name="expected_stamp_dashboard",
    ),
]
