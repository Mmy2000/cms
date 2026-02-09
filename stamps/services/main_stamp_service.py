from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.utils import timezone
from django.utils.dateparse import parse_date
from typing import Optional
from datetime import timedelta
from django.db.models import Sum, Q
from django.db.models.functions import TruncYear
from site_settings.models import SiteConfiguration
from stamps.admin import format_millions


class BaseStampService:

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
    def get_last_year(date_to):
        from datetime import datetime

        date_str = date_to[0]
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            return date_obj.year
        except:
            return None

    @staticmethod
    def get_this_month(queryset):
        now = timezone.now()

        # First day of current month
        first_day_current_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # First day of next month
        if now.month == 12:
            first_day_next_month = first_day_current_month.replace(
                year=now.year + 1, month=1
            )
        else:
            first_day_next_month = first_day_current_month.replace(month=now.month + 1)

        return queryset.filter(
            created_at__gte=first_day_current_month,
            created_at__lt=first_day_next_month,
        )

    @staticmethod
    def filter_by_date_range(queryset, date_from=None, date_to=None):
        filters = Q()

        if date_from:
            parsed_date = parse_date(date_from)
            if parsed_date:
                filters &= Q(invoice_date__gte=parsed_date)

        if date_to:
            parsed_date = parse_date(date_to)
            if parsed_date:
                filters &= Q(invoice_date__lte=parsed_date)

        return queryset.filter(filters) if filters else queryset

    @staticmethod
    def filter_by_years(queryset, years: int | None):
        if not years:
            return queryset

        start_date = timezone.now().date() - timedelta(days=365 * years)
        return queryset.filter(invoice_date__gte=start_date)

    @staticmethod
    def filter_by_user(queryset, user=None):
        if user:
            return queryset.filter(user=user)
        return queryset

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
        
        year = year or current_year or self.current_year

        if not self.retired_engineers or self.retired_engineers <= 0:
            return Decimal("0.00")

        try:
            current_total = self.total_amount(queryset) or Decimal("0")
            previous_total = self._total_for_previous_year(queryset, year) or Decimal(
                "0"
            )

            denominator = Decimal(self.retired_engineers) * Decimal(
                self.MONTHS_PER_YEAR
            )

            pension = (
                (current_total * self.PENSION_MULTIPLIER) + previous_total
            ) / denominator

            return pension.quantize(Decimal("0.01"))

        except (InvalidOperation, ZeroDivisionError, TypeError):
            return Decimal("0.00")

    @staticmethod
    def get_number_of_invoice_copies(
        queryset, entity_id: int, entity_field: str
    ) -> int:
        filter_kwargs = {entity_field: entity_id}
        result = queryset.filter(**filter_kwargs).aggregate(
            total_copies=Sum("invoice_copies")
        )["total_copies"]
        return result if result else 0

    @staticmethod
    def yearly_chart(queryset):
        stamps = (
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

        for item in stamps:
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
    def total_amount_for_entity(queryset, entity_id: int, entity_field: str) -> Decimal:
        filter_kwargs = {entity_field: entity_id}
        result = queryset.filter(**filter_kwargs).aggregate(total=Sum("d1"))["total"]
        return Decimal(str(result)) if result else Decimal("0")

    @staticmethod
    def total_entities(queryset, entity_field: str) -> int:
        return queryset.values(entity_field).distinct().count()
