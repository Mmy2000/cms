from django.db.models import Sum
from django.utils.dateparse import parse_date
from stamps.models import ExpectedStamp, Sector


class ExpectedStampService:

    @staticmethod
    def get_queryset():
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def filter(queryset, sector_id=None, date_from=None, date_to=None):
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)

        if date_from:
            queryset = queryset.filter(invoice_date__gte=parse_date(date_from))

        if date_to:
            queryset = queryset.filter(invoice_date__lte=parse_date(date_to))

        return queryset

    @staticmethod
    def sort(queryset, sort):
        if sort in ["invoice_date", "-invoice_date"]:
            return queryset.order_by(sort)
        return queryset.order_by("-created_at")

    @staticmethod
    def total_amount(queryset):
        return queryset.aggregate(total=Sum("d1"))["total"] or 0
    
    @staticmethod
    def total_sectors(queryset):
        return queryset.values("sector__name").distinct().count()
    
    @staticmethod
    def grouped_by_sector(queryset):
        return (
            queryset.values("sector__name", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def create_from_form(form):
        new_sector_name = form.cleaned_data.get("new_sector_name")
        sector = form.cleaned_data.get("sector")

        if new_sector_name:
            sector, _ = Sector.objects.get_or_create(name=new_sector_name)

        expected_stamp = form.save(commit=False)
        expected_stamp.sector = sector
        expected_stamp.save()

        return expected_stamp
