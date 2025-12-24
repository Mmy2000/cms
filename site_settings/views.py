from django.shortcuts import render
from stamps.models import StampCalculation
from stamps.services.expected_stamp_service import ExpectedStampService
from stamps.services.stamp_service import StampService
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from django.utils import timezone

# Create your views here.


def custom_404_view(request, exception=None):
    return render(request, "404.html", {}, status=404)


def dashboard(request):
    # Get filter parameter (default to 'all')
    time_filter = request.GET.get("filter", "all")

    # Calculate date range based on filter
    end_date = timezone.now().date()

    if time_filter == "last_year":
        start_date = end_date - timedelta(days=365)
    elif time_filter == "last_5_years":
        start_date = end_date - timedelta(days=365 * 5)
    elif time_filter == "last_10_years":
        start_date = end_date - timedelta(days=365 * 10)
    else:  # 'all'
        start_date = None

    # Filter querysets based on date range
    stamps = StampService.get_queryset()
    excepted_stamps = ExpectedStampService.get_queryset()

    if start_date:
        stamps = stamps.filter(invoice_date__gte=start_date)
        excepted_stamps = excepted_stamps.filter(invoice_date__gte=start_date)

    # Calculate totals
    total_stamps = StampService.total_amount(stamps)
    total_excepted_stamps = ExpectedStampService.total_amount(excepted_stamps)

    # Prepare chart data - aggregate by month
    stamps_by_month = (
        stamps.filter(invoice_date__isnull=False)
        .annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(total=Sum("total_stamp_for_company"))
        .order_by("month")
    )

    excepted_stamps_by_month = (
        excepted_stamps.filter(invoice_date__isnull=False)
        .annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(total=Sum("total_stamp_for_company"))
        .order_by("month")
    )

    # Format data for ApexCharts
    chart_categories = []
    stamp_data = []
    excepted_stamp_data = []

    # Create a unified list of all months
    all_months = set()
    for item in stamps_by_month:
        all_months.add(item["month"])
    for item in excepted_stamps_by_month:
        all_months.add(item["month"])

    all_months = sorted(list(all_months))

    # Create dictionaries for quick lookup
    stamps_dict = {item["month"]: item["total"] for item in stamps_by_month}
    excepted_dict = {item["month"]: item["total"] for item in excepted_stamps_by_month}

    # Build the chart data
    for month in all_months:
        # Format month for display (e.g., "Jan 2024")
        month_str = month.strftime("%b %Y")
        chart_categories.append(month_str)

        # Get values (default to 0 if not present)
        stamp_value = (
            float(stamps_dict.get(month, 0)) / 1_000_000
        )  # Convert to millions
        excepted_value = float(excepted_dict.get(month, 0)) / 1_000_000

        stamp_data.append(round(stamp_value, 2))
        excepted_stamp_data.append(round(excepted_value, 2))

    print(chart_categories, stamp_data, excepted_stamp_data)

    # If no data, provide empty arrays
    if not chart_categories:
        chart_categories = []
        stamp_data = []
        excepted_stamp_data = []

    context = {
        "total_stamps": total_stamps,
        "total_excepted_stamps": total_excepted_stamps,
        "chart_categories": chart_categories,
        "stamp_data": stamp_data,
        "excepted_stamp_data": excepted_stamp_data,
        "current_filter": time_filter,
    }

    return render(request, "index.html", context)

