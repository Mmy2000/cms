from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from stamps.models import StampCalculation, Company
from stamps.services.stamp.stamp_service import StampService
from .serializers import (
    StampCalculationSerializer,
    StampCalculationListSerializer,
    CompanySerializer,
)
from .pagination import StandardResultsPagination
from .facets import build_stamp_filters


class CompanyListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/companies/   – list all companies (supports ?search=)
    POST /api/companies/   – create a new company
    """

    serializer_class = CompanySerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return Company.objects.all()


class CompanyRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/companies/<pk>/  – retrieve a single company
    """

    serializer_class = CompanySerializer
    # permission_classes = [IsAuthenticated]
    queryset = Company.objects.all()


# ---------------------------------------------------------------------------
# Stamp Calculations
# ---------------------------------------------------------------------------


class StampListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/stamps/   – list stamp calculations with optional filters:
        ?company=<id>
        ?date_from=YYYY-MM-DD
        ?date_to=YYYY-MM-DD
        ?sort=-created_at | invoice_date | d1 | ...
        ?search=<company name>
        ?page=<n>

    POST /api/stamps/   – create a new stamp calculation
    """

    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["company__name", "note"]
    ordering_fields = ["created_at", "invoice_date", "d1", "total_stamp_for_company"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return StampCalculationListSerializer
        return StampCalculationSerializer

    def get_queryset(self):
        service = StampService()
        qs = service.get_queryset()
        qs = service.filter(
            qs,
            company_id=self.request.GET.get("company"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )
        return qs

    def list(self, request, *args, **kwargs):
        # base_qs = full unfiltered set, used for facet counts & date range
        service = StampService()
        base_qs = service.get_queryset()

        # filtered_qs = what the user actually asked for
        filtered_qs = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(filtered_qs)
        serializer = self.get_serializer(
            page if page is not None else filtered_qs, many=True
        )

        summary = {
            "total_all_companies": service.total_amount(filtered_qs),
        }

        facets = build_stamp_filters(
            base_qs=base_qs,
            active={
                "company": request.GET.get("company"),
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
        # create logic is inside the serializer
        serializer.save()


class StampRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/stamps/<pk>/   – detailed view of a single stamp record
                              includes per-company totals
    """

    serializer_class = StampCalculationSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StampCalculation.objects.select_related("company")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        service = StampService()
        qs = service.get_queryset()

        data = self.get_serializer(instance).data
        data["total_amount_for_company"] = service.total_amount_for_company(
            qs, instance.company_id
        )
        data["total_invoice_copies_for_company"] = service.get_number_of_invoice_copies(
            qs, instance.company_id
        )

        return Response(data)


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------


class StampExportAPIView(APIView):
    """
    GET /api/stamps/export/?format=pdf|excel
                           &company=<id>       (optional – company-specific PDF)
                           &date_from=YYYY-MM-DD
                           &date_to=YYYY-MM-DD
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        service = StampService()
        qs = service.get_queryset()
        qs = service.filter(
            qs,
            company_id=request.GET.get("company"),
            date_from=request.GET.get("date_from"),
            date_to=request.GET.get("date_to"),
        )

        export_format = request.GET.get("format", "excel").lower()
        company_id = request.GET.get("company")

        if export_format == "pdf":
            if company_id:
                try:
                    company_id = int(company_id)
                except (TypeError, ValueError):
                    return Response(
                        {"detail": "Invalid company id."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                file_data = service.export_to_pdf_for_spacific_company(
                    qs, company_id, user=request.user
                )
            else:
                file_data = service.export_pdf(qs)

            response = HttpResponse(file_data, content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=stamp_report.pdf"
            return response

        if export_format == "excel":
            file_data = service.export_excel_formatted(qs)
            response = HttpResponse(
                file_data,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = "attachment; filename=stamp_report.xlsx"
            return response

        return Response(
            {"detail": "Unsupported format. Use 'pdf' or 'excel'."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ---------------------------------------------------------------------------
# Dashboard / Summary endpoint
# ---------------------------------------------------------------------------


class StampDashboardAPIView(APIView):
    """
    GET /api/stamps/dashboard/?filter=all|last_3_year|last_5_years|last_7_years|last_10_years
    """

    # permission_classes = [IsAuthenticated]

    FILTER_MAP = {
        "last_3_year": 3,
        "last_5_years": 5,
        "last_7_years": 7,
        "last_10_years": 10,
    }

    def get(self, request, *args, **kwargs):
        service = StampService()
        time_filter = request.GET.get("filter", "all")
        years = None if time_filter == "all" else self.FILTER_MAP.get(time_filter)

        stamps = service.filter_by_years(service.get_queryset(), years)
        chart = service.yearly_chart(stamps)

        return Response(
            {
                "filter_applied": time_filter,
                "total_stamps": service.total_amount(stamps),
                "total_pension": service.calculate_pension(stamps),
                "chart": {
                    "categories": chart["categories"],
                    "yearly": chart["yearly"],
                    "cumulative": chart["cumulative"],
                },
            }
        )
