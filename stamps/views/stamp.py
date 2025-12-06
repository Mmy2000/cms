from django.views.generic import ListView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from .mixins import DateRangeFilterMixin, SortMixin, TotalAggregationMixin
from ..models import ExpectedStamp, Sector, StampCalculation, Company
from ..forms import ExpectedStampForm, StampCalculationForm


class StampListView(
    DateRangeFilterMixin,
    SortMixin,
    TotalAggregationMixin,
    ListView
):
    model = StampCalculation
    template_name = "stamp_list.html"
    context_object_name = "stamps"
    paginate_by = 10

    allowed_sorts = ["invoice_date", "-invoice_date"]

    def get_queryset(self):
        qs = (
            StampCalculation.objects
            .select_related("company")
        )

        # Company filter
        company_id = self.request.GET.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        qs = self.filter_by_date(qs)
        qs = self.apply_sort(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        context.update({
            "companies": Company.objects.all(),
            "company_filter": self.request.GET.get("company"),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort_by": self.request.GET.get("sort", self.default_sort),
            "total_all_companies": self.get_total(qs),
        })
        return context


class StampCreateView(SuccessMessageMixin, CreateView):
    model = StampCalculation
    form_class = StampCalculationForm
    template_name = "add_stamp.html"
    success_url = reverse_lazy("stamp_list")
    success_message = "تمت إضافة حساب الدمغة بنجاح."

    def form_valid(self, form):
        new_company_name = form.cleaned_data.get("new_company_name")
        company = form.cleaned_data.get("company")

        if new_company_name:
            company, _ = Company.objects.get_or_create(name=new_company_name)

        stamp = form.save(commit=False)
        stamp.company = company
        stamp.save()

        return super().form_valid(form)
