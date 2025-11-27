from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnfoldModelAdmin


def format_millions(value):
    """Helper: format numbers in millions."""
    if value is None:
        return "-"
    try:
        value = float(value)
    except:
        return value

    if value >= 1_000_000:
        return f"{round(value / 1_000_000, 2)}M"

    return f"{int(value):,}"


@admin.register(Company)
class CompanyAdmin(UnfoldModelAdmin):
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
        "total_display",
        "created_at",
    ]
    readonly_fields = ["created_at", "total_past_years", "total_stamp_for_company", "d1"]

    search_fields = ["company__name"]
    list_filter = ["invoice_date", "company"]
    ordering = ["-created_at"]

    # --- Custom display methods ---
    def value_of_work_display(self, obj):
        return format_millions(obj.value_of_work)

    value_of_work_display.short_description = "قيمه الاعمال"

    def d1_display(self, obj):
        return format_millions(obj.d1)

    d1_display.short_description = "إجمالي الدمغه للمطالبة"

    def past_display(self, obj):
        return format_millions(obj.total_past_years)

    past_display.short_description = "رصيد سنوات سابقة"

    def total_display(self, obj):
        return format_millions(obj.total_stamp_for_company)

    total_display.short_description = "اجمالي الدمغه"
