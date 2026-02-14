from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from stamps.services.expected_stamp.expected_stamp_service import ExpectedStampService

from stamps.models import ExpectedStamp, Sector
from .serializers import (
    ExpectedStampSerializer,
    ExpectedStampListSerializer,
    SectorSerializer,
)
from .pagination import StandardResultsPagination
from .facets import build_expected_stamp_filters


class SectorListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/sectors/   – list all sectors (supports ?search=)
    POST /api/sectors/   – create a new sector
    """

    serializer_class = SectorSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return Sector.objects.all()


class SectorRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/sectors/<pk>/   – retrieve a single sector
    """

    serializer_class = SectorSerializer
    # permission_classes = [IsAuthenticated]
    queryset = Sector.objects.all()


# ---------------------------------------------------------------------------
# Expected Stamps
# ---------------------------------------------------------------------------


class ExpectedStampListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/expected-stamps/   – list expected stamps with optional filters:
        ?sector=<id>
        ?date_from=YYYY-MM-DD
        ?date_to=YYYY-MM-DD
        ?sort=-created_at | invoice_date | d1 | ...
        ?search=<sector name>
        ?page=<n>

    POST /api/expected-stamps/   – create a new expected stamp record
    """

    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["sector__name", "note"]
    ordering_fields = ["created_at", "invoice_date", "d1", "total_stamp_for_company"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ExpectedStampListSerializer
        return ExpectedStampSerializer

    def get_queryset(self):
        service = ExpectedStampService()
        qs = service.get_queryset()
        qs = service.filter(
            qs,
            sector_id=self.request.GET.get("sector"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )
        return qs

    def list(self, request, *args, **kwargs):
        # base_qs = full unfiltered set, used for facet counts & date range
        service = ExpectedStampService()
        base_qs = service.get_queryset()

        # filtered_qs = what the user actually asked for
        filtered_qs = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(filtered_qs)
        serializer = self.get_serializer(
            page if page is not None else filtered_qs, many=True
        )

        summary = {
            "total_all_sectors": service.total_amount(filtered_qs),
        }

        facets = build_expected_stamp_filters(
            base_qs=base_qs,
            active={
                "sector": request.GET.get("sector"),
                "date_from": request.GET.get("date_from"),
                "date_to": request.GET.get("date_to"),
                "search": request.GET.get("search"),
                "ordering": request.GET.get("ordering"),
            },
        )

        payload = {"results": serializer.data, "summary": summary, "filters": facets}

        if page is not None:
            return self.get_paginated_response(payload)

        return Response(payload)

    def perform_create(self, serializer):
        serializer.save()


class ExpectedStampRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/expected-stamps/<pk>/   – detailed view of a single expected stamp record
                                       includes per-sector totals
    """

    serializer_class = ExpectedStampSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExpectedStamp.objects.select_related("sector")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        service = ExpectedStampService()
        qs = service.get_queryset()

        data = self.get_serializer(instance).data
        data["total_amount_for_sector"] = service.total_amount_for_sector(
            qs, instance.sector_id
        )
        data["total_invoice_copies_for_company"] = service.get_number_of_invoice_copies(
            qs, instance.sector_id
        )

        return Response(data)
