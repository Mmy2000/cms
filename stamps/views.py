from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import StampCalculationForm
from .models import StampCalculation, Company
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
