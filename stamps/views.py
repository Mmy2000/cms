from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ExpectedStampForm, StampCalculationForm
from .models import ExpectedStamp, Sector, StampCalculation, Company
from django.db.models import Sum
from django.core.paginator import Paginator


def stamp_list(request):

    company_filter = request.GET.get("company")

    stamps = StampCalculation.objects.select_related("company")

    if company_filter:
        stamps = stamps.filter(company__id=company_filter)

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    allowed_sorts = ["invoice_date", "-invoice_date"]

    if sort_by in allowed_sorts:
        stamps = stamps.order_by(sort_by)
    else:
        sort_by = "-created_at"
        stamps = stamps.order_by(sort_by)

    # Total
    total_all_companies = stamps.aggregate(total=Sum("d1"))["total"] or 0

    # ⭐ Pagination
    page_number = request.GET.get("page")
    paginator = Paginator(stamps, 10)  # ← number of rows per page
    page_obj = paginator.get_page(page_number)

    companies = Company.objects.all()

    context = {
        "page_obj": page_obj,  # ← send page_obj instead of stamps
        "stamps": page_obj,  # optional for easier usage in template
        "companies": companies,
        "total_all_companies": total_all_companies,
        "company_filter": company_filter,
        "sort_by": sort_by,
    }

    return render(request, "stamp_list.html", context)


def add_stamp(request):
    if request.method == "POST":
        form = StampCalculationForm(request.POST)

        if form.is_valid():
            # Extract new company fields
            new_company_name = form.cleaned_data.get("new_company_name")

            # Selected company from dropdown
            company = form.cleaned_data.get("company")

            # If the user entered a new company → create it and replace the selected one
            if new_company_name :
                company, created = Company.objects.get_or_create(
                    name=new_company_name,
                )

            # Save stamp record
            stamp = form.save(commit=False)
            stamp.company = company
            stamp.save()  # Triggers automatic d1, totals calculation

            messages.success(request, "تمت إضافة حساب الدمغة بنجاح.")
            return redirect("stamp_list")

    else:
        form = StampCalculationForm()

    return render(request, "add_stamp.html", {"form": form})


def expected_stamp_list(request):
    sector_filter = request.GET.get("sector")
    expected_stamps = ExpectedStamp.objects.select_related("sector").order_by("-created_at")
    if sector_filter:
        expected_stamps = expected_stamps.filter(sector__id=sector_filter)

    # sorting
    sort_by = request.GET.get("sort", "-created_at")
    allowed_sorts = ["invoice_date", "-invoice_date"]

    if sort_by in allowed_sorts:
        expected_stamps = expected_stamps.order_by(sort_by)
    else:
        sort_by = "-created_at"
        expected_stamps = expected_stamps.order_by(sort_by)

    # total
    total_all_sectors = expected_stamps.aggregate(total=Sum("d1"))["total"] or 0

    # ⭐ Pagination
    page_number = request.GET.get("page")
    paginator = Paginator(expected_stamps, 10)  # ← number of rows per page
    page_obj = paginator.get_page(page_number)

    sectors = Sector.objects.all()

    context = {
        "page_obj": page_obj,  # ← send page_obj instead of stamps
        "expected_stamps": page_obj,  # optional for easier usage in template
        "sectors": sectors,
        "total_all_sectors": total_all_sectors,
        "sector_filter": sector_filter,
        "sort_by": sort_by,
    }

    return render(request, "expected_stamp_list.html", context)

def add_expected_stamp(request):
    if request.method == "POST":
        form = ExpectedStampForm(request.POST)

        if form.is_valid():
            # Extract new sector fields
            new_sector_name = form.cleaned_data.get("new_sector_name")

            # Selected sector from dropdown
            sector = form.cleaned_data.get("sector")

            # If the user entered a new sector → create it and replace the selected one
            if new_sector_name :
                sector, created = Sector.objects.get_or_create(
                    name=new_sector_name,
                )

            # Save expected stamp record
            expected_stamp = form.save(commit=False)
            expected_stamp.sector = sector
            expected_stamp.save()  # Triggers automatic d1, totals calculation

            messages.success(request, "تمت إضافة حساب الدمغة المتوقعة بنجاح.")
            return redirect("expected_stamp_list")

    else:
        form = ExpectedStampForm()

    return render(request, "add_expected_stamp.html", {"form": form})