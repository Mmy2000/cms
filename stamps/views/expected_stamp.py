from django.views.generic import ListView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .mixins import DateRangeFilterMixin, SortMixin, TotalAggregationMixin
from ..models import ExpectedStamp, Sector
from ..forms import ExpectedStampForm


class ExpectedStampListView(
    DateRangeFilterMixin, SortMixin, TotalAggregationMixin, ListView
):
    model = ExpectedStamp
    template_name = "expected_stamp_list.html"
    context_object_name = "expected_stamps"
    paginate_by = 10

    allowed_sorts = ["invoice_date", "-invoice_date"]

    def get_queryset(self):
        qs = ExpectedStamp.objects.select_related("sector")

        sector_id = self.request.GET.get("sector")
        if sector_id:
            qs = qs.filter(sector_id=sector_id)

        qs = self.filter_by_date(qs)
        qs = self.apply_sort(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        context.update(
            {
                "sectors": Sector.objects.all(),
                "sector_filter": self.request.GET.get("sector"),
                "total_all_sectors": self.get_total(qs),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": self.request.GET.get("date_to", ""),
            }
        )
        return context


class ExpectedStampCreateView(SuccessMessageMixin, CreateView):
    model = ExpectedStamp
    form_class = ExpectedStampForm
    template_name = "add_expected_stamp.html"
    success_url = reverse_lazy("expected_stamp_list")
    success_message = "تمت إضافة حساب الدمغة المتوقعة بنجاح."

    def form_valid(self, form):
        new_sector_name = form.cleaned_data.get("new_sector_name")
        sector = form.cleaned_data.get("sector")

        if new_sector_name:
            sector, _ = Sector.objects.get_or_create(name=new_sector_name)

        expected_stamp = form.save(commit=False)
        expected_stamp.sector = sector
        expected_stamp.save()

        return super().form_valid(form)
