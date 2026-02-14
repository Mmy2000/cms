from django.urls import path
from .stamp_views import (
    CompanyListCreateAPIView,
    CompanyRetrieveAPIView,
    StampListCreateAPIView,
    StampRetrieveAPIView,
    StampExportAPIView,
    StampDashboardAPIView,
)
from .expected_stamp_views import (
    SectorListCreateAPIView,
    SectorRetrieveAPIView,
    ExpectedStampListCreateAPIView,
    ExpectedStampRetrieveAPIView,
)

urlpatterns = [
    # ── Companies ──────────────────────────────────────────────────────────
    path("companies/", CompanyListCreateAPIView.as_view(), name="api-company-list"),
    path("companies/<int:pk>/", CompanyRetrieveAPIView.as_view(), name="api-company-detail"),

    # ── Stamp Calculations ─────────────────────────────────────────────────
    path("stamps/", StampListCreateAPIView.as_view(), name="api-stamp-list"),
    path("stamps/<int:pk>/", StampRetrieveAPIView.as_view(), name="api-stamp-detail"),
    path("stamps/export/", StampExportAPIView.as_view(), name="api-stamp-export"),
    path("stamps/dashboard/", StampDashboardAPIView.as_view(), name="api-stamp-dashboard"),

    # ── Sectors ────────────────────────────────────────────────────────────
    path("sectors/", SectorListCreateAPIView.as_view(), name="api-sector-list"),
    path("sectors/<int:pk>/", SectorRetrieveAPIView.as_view(), name="api-sector-detail"),

    # ── Expected Stamps ────────────────────────────────────────────────────
    path("expected-stamps/", ExpectedStampListCreateAPIView.as_view(), name="api-expected-stamp-list"),
    path("expected-stamps/<int:pk>/", ExpectedStampRetrieveAPIView.as_view(), name="api-expected-stamp-detail"),
]