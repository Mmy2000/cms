from stamps.models import ExpectedStamp, Sector
from django.db.models import Sum, Q
from typing import Optional
from decimal import Decimal
from stamps.services.main_stamp_service import BaseStampService
from .expected_stamp_excel_service import ExpectedStampExcelService
from .expected_stamp_pdf_service import ExpectedStampPDFService


class ExpectedStampService(BaseStampService):

    @staticmethod
    def get_queryset():
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def get_expected_stamp_by_id(stamp_id: int) -> Optional[ExpectedStamp]:
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
        queryset = cls.get_queryset()
        queryset = cls.filter(queryset, sector_id, date_from, date_to)
        return cls.sort(queryset, sort)

    @staticmethod
    def filter(queryset, sector_id=None, date_from=None, date_to=None, user=None):
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
        return BaseStampService.total_entities(queryset, "sector_id")

    @staticmethod
    def total_amount_for_sector(queryset, sector_id: int) -> Decimal:
        return BaseStampService.total_amount_for_entity(
            queryset, sector_id, "sector_id"
        )

    @staticmethod
    def grouped_by_sector(queryset):
        return (
            queryset.values("sector__name", "sector_id", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def get_number_of_invoice_copies(queryset, sector_id: int) -> int:
        return BaseStampService.get_number_of_invoice_copies(
            queryset, sector_id, "sector_id"
        )

    @staticmethod
    def create_from_form(form, user):
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

    @staticmethod
    def export_pdf(queryset):
        return ExpectedStampPDFService.export_general_report(queryset)

    @staticmethod
    def export_to_pdf_for_spacific_sector(queryset, sector_id, user=None):
        return ExpectedStampPDFService.export_sector_detailed_report(
            queryset, sector_id, user
        )

    @staticmethod
    def export_excel(queryset):
        return ExpectedStampExcelService.export_basic_report(queryset)

    @staticmethod
    def export_excel_formatted(queryset):
        return ExpectedStampExcelService.export_formatted_report(queryset)

    @staticmethod
    def export_excel_sector_summary(queryset):
        return ExpectedStampExcelService.export_sector_summary_report(queryset)