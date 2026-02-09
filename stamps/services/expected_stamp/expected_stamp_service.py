from stamps.models import ExpectedStamp, Sector
from django.db.models import Sum, Q
from typing import Optional
from decimal import Decimal
from stamps.services.main_stamp_service import BaseStampService
from .expected_stamp_excel_service import ExpectedStampExcelService
from .expected_stamp_pdf_service import ExpectedStampPDFService


class ExpectedStampService(BaseStampService):
    """
    Business logic for ExpectedStamp calculations with improved error handling,
    performance optimizations, and better separation of concerns.

    Inherits common functionality from BaseStampService.
    """

    @staticmethod
    def get_queryset():
        """Get base queryset with related sector data."""
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def get_expected_stamp_by_id(stamp_id: int) -> Optional[ExpectedStamp]:
        """Retrieve a single expected stamp by ID."""
        try:
            return ExpectedStamp.objects.select_related("sector").get(id=stamp_id)
        except ExpectedStamp.DoesNotExist:
            return None

    @classmethod
    def get_filtered_queryset(
        cls,
        sector_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort: str = "-created_at",
    ):
        """Get filtered and sorted queryset based on provided parameters."""
        queryset = cls.get_queryset()
        queryset = cls.filter(queryset, sector_id, date_from, date_to)
        return cls.sort(queryset, sort)

    @staticmethod
    def filter(queryset, sector_id=None, date_from=None, date_to=None, user=None):
        """
        Filter queryset by sector, date range, and user.
        Combines base date filtering with sector-specific logic.
        """
        filters = Q()

        # Sector filter
        if sector_id and str(sector_id).lower() not in ["none", ""]:
            filters &= Q(sector_id=sector_id)

        # Apply base filters
        queryset = BaseStampService.filter_by_date_range(queryset, date_from, date_to)
        queryset = BaseStampService.filter_by_user(queryset, user)

        return queryset.filter(filters) if filters else queryset

    @staticmethod
    def total_sectors(queryset) -> int:
        """Count distinct sectors in queryset."""
        return BaseStampService.total_entities(queryset, "sector_id")

    @staticmethod
    def total_amount_for_sector(queryset, sector_id: int) -> Decimal:
        """Calculate total amount for a specific sector."""
        return BaseStampService.total_amount_for_entity(
            queryset, sector_id, "sector_id"
        )

    @staticmethod
    def grouped_by_sector(queryset):
        """Group expected stamps by sector with totals."""
        return (
            queryset.values("sector__name", "sector_id", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def get_number_of_invoice_copies(queryset, sector_id: int) -> int:
        """Get total invoice copies for a specific sector."""
        return BaseStampService.get_number_of_invoice_copies(
            queryset, sector_id, "sector_id"
        )

    @staticmethod
    def create_from_form(form, user):
        """
        Create a new ExpectedStamp from form data.
        Handles both existing sectors and new sector creation.
        """
        new_sector_name = form.cleaned_data.get("new_sector_name", "").strip()
        sector = form.cleaned_data.get("sector")

        if new_sector_name:
            sector, created = Sector.objects.get_or_create(
                name__iexact=new_sector_name, defaults={"name": new_sector_name}
            )

        if not sector:
            raise ValueError("Either sector or new_sector_name must be provided")

        expected_stamp = form.save(commit=False)
        expected_stamp.sector = sector
        expected_stamp.user = user
        expected_stamp.save()

        return expected_stamp

    # Export methods delegating to specialized services

    @staticmethod
    def export_pdf(queryset):
        """Export general PDF report."""
        return ExpectedStampPDFService.export_general_report(queryset)

    @staticmethod
    def export_to_pdf_for_spacific_sector(queryset, sector_id, user=None):
        """Export detailed PDF report for specific sector."""
        return ExpectedStampPDFService.export_sector_detailed_report(
            queryset, sector_id, user
        )

    @staticmethod
    def export_pdf_to_judicial_seizure(queryset):
        """Export PDF for judicial seizure (not yet implemented)."""
        pass

    @staticmethod
    def export_excel(queryset):
        """Export basic Excel report."""
        return ExpectedStampExcelService.export_basic_report(queryset)

    @staticmethod
    def export_excel_formatted(queryset):
        """Export formatted Excel report."""
        return ExpectedStampExcelService.export_formatted_report(queryset)

    @staticmethod
    def export_excel_sector_summary(queryset):
        """Export sector summary Excel report."""
        return ExpectedStampExcelService.export_sector_summary_report(queryset)
