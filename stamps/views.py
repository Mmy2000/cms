from django.shortcuts import render
from .models import StampCalculation, Company
from django.db.models import Sum


def stamp_list(request):

    # ========== الفلاتر ==========
    company_filter = request.GET.get("company")

    stamps = StampCalculation.objects.select_related("company")

    if company_filter:
        stamps = stamps.filter(company__id=company_filter)

    # ========== الترتيب Sorting ==========
    sort_by = request.GET.get("sort", "-created_at")

    allowed_sorts = [
        "company__name",
        "-company__name",
        "company__year",
        "-company__year",
        "value_of_work",
        "-value_of_work",
        "invoice_copies",
        "-invoice_copies",
        "stamp_rate",
        "-stamp_rate",
        "d1",
        "-d1",
        "total_past_years",
        "-total_past_years",
        "total_stamp_for_company",
        "-total_stamp_for_company",
        "created_at",
        "-created_at",
    ]

    if sort_by in allowed_sorts:
        stamps = stamps.order_by(sort_by)
    else:
        sort_by = "-created_at"
        stamps = stamps.order_by(sort_by)

    # ========== إجمالي الدمغات ==========
    total_all_companies = (
        stamps.aggregate(total=Sum("total_stamp_for_company"))["total"] or 0
    )

    companies = Company.objects.all()

    context = {
        "stamps": stamps,
        "companies": companies,
        "total_all_companies": total_all_companies,
        "company_filter": company_filter,
        "sort_by": sort_by,
    }

    return render(request, "stamp_list.html", context)
