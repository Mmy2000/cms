from django.db.models import Sum
from django.utils.dateparse import parse_date


class DateRangeFilterMixin:
    date_field = "invoice_date"

    def filter_by_date(self, queryset):
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if date_from:
            queryset = queryset.filter(
                **{f"{self.date_field}__gte": parse_date(date_from)}
            )

        if date_to:
            queryset = queryset.filter(
                **{f"{self.date_field}__lte": parse_date(date_to)}
            )

        return queryset


class SortMixin:
    allowed_sorts = []
    default_sort = "-created_at"

    def apply_sort(self, queryset):
        sort = self.request.GET.get("sort", self.default_sort)
        if sort in self.allowed_sorts:
            return queryset.order_by(sort)
        return queryset.order_by(self.default_sort)


class TotalAggregationMixin:
    total_field = "d1"

    def get_total(self, queryset):
        return queryset.aggregate(total=Sum(self.total_field))["total"] or 0
