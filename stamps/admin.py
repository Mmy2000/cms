from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin as UnfoldModelAdmin


@admin.register(Company)
class CompanyAdmin(UnfoldModelAdmin):
    list_display = ["name", "year"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(StampCalculation)
class StampCalculationAdmin(UnfoldModelAdmin):
    list_display = ["company", "value_of_work", "invoice_copies", "stamp_rate", "d1", "total_past_years", "total_stamp_for_company", "created_at"]
    search_fields = ["company", "year"]
    ordering = ["-created_at"]
