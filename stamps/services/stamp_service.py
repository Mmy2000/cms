from django.db.models import Sum
from django.utils.dateparse import parse_date
from stamps.models import StampCalculation, Company


class StampService:
    """
    Business logic for StampCalculation
    """

    @staticmethod
    def get_queryset():
        return StampCalculation.objects.select_related("company")

    @staticmethod
    def filter(queryset, company_id=None, date_from=None, date_to=None):
        if company_id:
            queryset = queryset.filter(company_id=company_id)

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
    def total_companies(queryset):
        return queryset.values("company__name").distinct().count()

    @staticmethod
    def grouped_by_company(queryset):
        return (
            queryset.values("company__name", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def create_from_form(form):
        """
        Create stamp + handle new company logic
        """
        new_company_name = form.cleaned_data.get("new_company_name")
        company = form.cleaned_data.get("company")

        if new_company_name:
            company, _ = Company.objects.get_or_create(name=new_company_name)

        stamp = form.save(commit=False)
        stamp.company = company
        stamp.save()

        return stamp
