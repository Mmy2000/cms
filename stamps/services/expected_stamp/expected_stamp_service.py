from site_settings.models import SiteConfiguration
from stamps.admin import format_millions
from stamps.models import ExpectedStamp, Sector
from datetime import date, datetime,timedelta
from django.db.models import Sum, Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from typing import Optional
from django.db.models.functions import TruncYear
from decimal import Decimal, ROUND_HALF_UP,InvalidOperation
from typing import Optional
from .expected_stamp_excel_service import ExpectedStampExcelService
from .expected_stamp_pdf_service import ExpectedStampPDFService


class ExpectedStampService:
    """
    Business logic for ExpectedStamp calculations with improved error handling,
    performance optimizations, and better separation of concerns.
    """

    PREVIOUS_YEAR_MULTIPLIER = Decimal("0.7")
    PENSION_MULTIPLIER = Decimal("0.2")
    MONTHS_PER_YEAR = 12

    def __init__(self, retired_engineers: Optional[int] = None):
        if retired_engineers is None:
            config = SiteConfiguration.objects.only(
                "number_of_retired_engineers"
            ).first()
            retired_engineers = (
                getattr(config, "number_of_retired_engineers", 0) if config else 0
            )
        self.retired_engineers = retired_engineers or 0
        self.current_year = timezone.now().year

    @staticmethod
    def get_queryset():
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def get_expected_stamp_by_id(stamp_id: int) -> Optional[ExpectedStamp]:
        try:
            return ExpectedStamp.objects.select_related("sector").get(id=stamp_id)
        except ExpectedStamp.DoesNotExist:
            return None

    @staticmethod
    def get_last_year(date_to):
        date_str = date_to[0]
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            last_year = date_obj.year
        except:
            return None

        return last_year

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
    def filter(queryset, sector_id=None, date_from=None, date_to=None,user=None):
        filters = Q()

        if sector_id and str(sector_id).lower() not in ["none", ""]:
            filters &= Q(sector_id=sector_id)

        if date_from:
            parsed_date = parse_date(date_from)
            if parsed_date:
                filters &= Q(invoice_date__gte=parsed_date)

        if date_to:
            parsed_date = parse_date(date_to)
            if parsed_date:
                filters &= Q(invoice_date__lte=parsed_date)

        if user:
            filters &= Q(user=user)

        return queryset.filter(filters) if filters else queryset

    @staticmethod
    def filter_by_years(queryset, years: int | None):
        if not years:
            return queryset

        start_date = timezone.now().date() - timedelta(days=365 * years)
        return queryset.filter(invoice_date__gte=start_date)

    @staticmethod
    def sort(queryset, sort: str = "-created_at"):
        allowed_sorts = ["invoice_date", "-invoice_date", "created_at", "-created_at"]
        return queryset.order_by(sort if sort in allowed_sorts else "-created_at")

    @staticmethod
    def total_amount(queryset) -> Decimal:
        result = queryset.aggregate(total=Sum("d1"))["total"]
        return Decimal(str(result)) if result else Decimal("0")

    def _total_for_previous_year(
        self, queryset, current_year: Optional[int] = None
    ) -> Decimal:

        year = current_year if current_year is not None else self.current_year
        previous_year = year - 1

        stamps = queryset.filter(invoice_date__year=previous_year)
        total = stamps.aggregate(total=Sum("d1"))["total"]

        if not total:
            return Decimal("0")

        return Decimal(str(total)) * self.PREVIOUS_YEAR_MULTIPLIER

    def get_30_from_previous_year(self, queryset) -> Decimal:

        year = self.current_year
        previous_year = year - 1

        stamps = queryset.filter(invoice_date__year=previous_year)
        total = stamps.aggregate(total=Sum("d1"))["total"]

        if not total:
            return Decimal("0")

        return Decimal(str(total)) * Decimal("0.3")

    def calculate_pension(
        self,
        queryset,
        year: Optional[int] = None,
        current_year: Optional[int] = None,
    ) -> Decimal:
        """
        Safely calculate pension without raising runtime errors.
        """

        # Resolve year safely
        year = year or current_year or self.current_year

        # Protect against invalid retired_engineers
        if not self.retired_engineers or self.retired_engineers <= 0:
            return Decimal("0.00")

        try:
            current_total = self.total_amount(queryset) or Decimal("0")
            previous_total = self._total_for_previous_year(queryset, year) or Decimal("0")

            denominator = Decimal(self.retired_engineers) * Decimal(self.MONTHS_PER_YEAR)

            pension = (
                (current_total * self.PENSION_MULTIPLIER) + previous_total
            ) / denominator

            return pension

        except (ZeroDivisionError, TypeError, InvalidOperation):
            return Decimal("0.00")

    @staticmethod
    def total_sectors(queryset) -> int:
        return queryset.values("sector_id").distinct().count()

    @staticmethod
    def total_amount_for_sector(queryset, sector_id: int) -> Decimal:
        result = queryset.filter(sector_id=sector_id).aggregate(total=Sum("d1"))[
            "total"
        ]
        return Decimal(str(result)) if result else Decimal("0")

    @staticmethod
    def grouped_by_sector(queryset):
        return (
            queryset.values("sector__name", "sector_id", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def get_number_of_invoice_copies(queryset, sector_id: int) -> int:
        result = queryset.filter(sector_id=sector_id).aggregate(
            total_copies=Sum("invoice_copies")
        )["total_copies"]
        return result if result else 0

    @staticmethod
    def yearly_chart(queryset):
        expected_stamps = (
            queryset.filter(invoice_date__isnull=False)
            .annotate(year=TruncYear("invoice_date"))
            .values("year")
            .annotate(total=Sum("d1"))
            .order_by("year")
        )

        categories = []
        yearly = []
        cumulative = []

        running_total = 0

        for item in expected_stamps:
            year = item["year"].strftime("%Y")
            value = round(float(item["total"]), 2)

            categories.append(year)
            yearly.append(value)

            running_total += value
            cumulative.append(round(running_total, 2))

        yearly = [format_millions(v) for v in yearly]
        cumulative = [format_millions(v) for v in cumulative]

        return {
            "categories": categories,
            "yearly": yearly,
            "cumulative": cumulative,
        }

    @staticmethod
    def create_from_form(form,user):
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
    def export_to_pdf_for_spacific_sector(queryset, sector_id):
        return ExpectedStampPDFService.export_sector_detailed_report(
            queryset, sector_id
        )

    @staticmethod
    def export_pdf_to_judicial_seizure(queryset):
        pass

    @staticmethod
    def export_excel(queryset):
        return ExpectedStampExcelService.export_basic_report(queryset)

    @staticmethod
    def export_excel_formatted(queryset):
        return ExpectedStampExcelService.export_formatted_report(queryset)

    @staticmethod
    def export_excel_sector_summary(queryset):
        return ExpectedStampExcelService.export_sector_summary_report(queryset)
