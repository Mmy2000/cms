from django.utils.dateparse import parse_date
from stamps.models import StampCalculation, Company
from django.db.models import Sum, Q
from typing import Optional
from decimal import Decimal
from stamps.services.main_stamp_service import BaseStampService
from .stamp_pdf_service import StampPDFService
from .stamp_excel_service import StampExcelService


class StampService(BaseStampService):

    @staticmethod
    def get_queryset():
        return StampCalculation.objects.select_related("company")

    @staticmethod
    def get_stamp_by_id(stamp_id: int) -> Optional[StampCalculation]:
        try:
            return StampCalculation.objects.select_related("company").get(id=stamp_id)
        except StampCalculation.DoesNotExist:
            return None

    @staticmethod
    def filter(queryset, company_id=None, date_from=None, date_to=None, user=None):
        filters = Q()

        # Company filter
        if company_id and str(company_id).lower() not in ["none", ""]:
            filters &= Q(company_id=company_id)

        # Apply base filters
        queryset = BaseStampService.filter_by_date_range(queryset, date_from, date_to)
        queryset = BaseStampService.filter_by_user(queryset, user)

        return queryset.filter(filters) if filters else queryset

    @staticmethod
    def total_companies(queryset) -> int:
        return BaseStampService.total_entities(queryset, "company_id")

    @staticmethod
    def total_amount_for_company(queryset, company_id: int) -> Decimal:
        return BaseStampService.total_amount_for_entity(
            queryset, company_id, "company_id"
        )

    @staticmethod
    def grouped_by_company(queryset):
        return (
            queryset.values(
                "company__name", "company_id", "stamp_rate", "invoice_copies"
            )
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def get_number_of_invoice_copies(queryset, company_id: int) -> int:
        return BaseStampService.get_number_of_invoice_copies(
            queryset, company_id, "company_id"
        )

    @staticmethod
    def create_from_form(form, user):
        new_company_name = form.cleaned_data.get("new_company_name", "").strip()
        company = form.cleaned_data.get("company")

        if new_company_name:
            company, created = Company.objects.get_or_create(
                name__iexact=new_company_name, defaults={"name": new_company_name}
            )

        if not company:
            raise ValueError("Either company or new_company_name must be provided")

        stamp = form.save(commit=False)
        stamp.company = company
        stamp.user = user
        stamp.save()

        return stamp

    @staticmethod
    def export_pdf(queryset):
        return StampPDFService.export_general_report(queryset)

    @staticmethod
    def export_to_pdf_for_spacific_company(queryset, company_id, user=None):
        return StampPDFService.export_company_detailed_report(
            queryset, company_id, user
        )

    @staticmethod
    def export_excel(queryset):
        return StampExcelService.export_basic_report(queryset)

    @staticmethod
    def export_excel_formatted(queryset):
        return StampExcelService.export_formatted_report(queryset)

    @staticmethod
    def export_excel_company_summary(queryset):
        return StampExcelService.export_company_summary_report(queryset)