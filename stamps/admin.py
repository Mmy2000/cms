from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnfoldModelAdmin


def format_millions(value):
    """
    Convert large numbers to millions (numeric).
    Always returns a float.

    Examples:
    1_500_000 -> 1.5
    500_000   -> 500000.0
    None      -> 0.0
    """
    if value is None:
        return 0.0

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    return round(value / 1_000_000, 2)


@admin.register(Company)
class CompanyAdmin(UnfoldModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]

@admin.register(Sector)
class SectorAdmin(UnfoldModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]

@admin.register(StampCalculation)
class StampCalculationAdmin(UnfoldModelAdmin):
    list_display = [
        "company",
        "invoice_date",
        "value_of_work_display",
        "invoice_copies",
        "stamp_rate",
        "d1_display",
        "past_display",
        # "total_display",
        "created_at",
    ]
    readonly_fields = ["created_at", "total_past_years", "total_stamp_for_company", "d1"]

    search_fields = ["company__name"]
    list_filter = ["invoice_date", "company"]

    # --- Custom display methods ---
    def value_of_work_display(self, obj):
        return format_millions(obj.value_of_work)

    value_of_work_display.short_description = "قيمه الاعمال"
    value_of_work_display.admin_order_field = "value_of_work"

    def d1_display(self, obj):
        return format_millions(obj.d1)

    d1_display.short_description = "إجمالي الدمغه للمطالبة"

    def past_display(self, obj):
        return format_millions(obj.total_past_years)

    past_display.short_description = "رصيد سنوات سابقة"

    def total_display(self, obj):
        return format_millions(obj.total_stamp_for_company)

    total_display.short_description = "اجمالي الدمغه"


@admin.register(ExpectedStamp)
class ExpectedStampAdmin(UnfoldModelAdmin):
    list_display = [
        "sector",
        "invoice_date",
        "value_of_work_display",
        "invoice_copies",
        "stamp_rate",
        "d1_display",
        "past_display",
        # "total_display",
        "created_at",
    ]
    readonly_fields = ["created_at", "total_past_years", "total_stamp_for_company", "d1"]

    search_fields = ["sector__name"]
    list_filter = ["sector"]
    ordering = ["-created_at","value_of_work"]

    # --- Custom display methods ---
    def value_of_work_display(self, obj):
        return format_millions(obj.value_of_work)

    value_of_work_display.short_description = "قيمه الاعمال"
    value_of_work_display.admin_order_field = "value_of_work"

    def d1_display(self, obj):
        return format_millions(obj.d1)

    d1_display.short_description = "إجمالي الدمغه للمطالبة"

    def past_display(self, obj):
        return format_millions(obj.total_past_years)

    past_display.short_description = "رصيد سنوات سابقة"

    def total_display(self, obj):
        return format_millions(obj.total_stamp_for_company)

    total_display.short_description = "اجمالي الدمغه"
