from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin

from ..forms import StampCalculationForm
from ..models import Company
from ..services.stamp_service import StampService


class StampListView(ListView):
    template_name = "stamps/stamp_list.html"
    context_object_name = "stamps"
    paginate_by = 10

    def get_queryset(self):
        qs = StampService.get_queryset()

        qs = StampService.filter(
            qs,
            company_id=self.request.GET.get("company"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )

        qs = StampService.sort(
            qs,
            self.request.GET.get("sort")
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list

        context.update({
            "companies": Company.objects.all(),
            "company_filter": self.request.GET.get("company"),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort_by": self.request.GET.get("sort", "-created_at"),
            "total_all_companies": StampService.total_amount(qs),
        })
        return context


class GroupedStampListView(ListView):
    template_name = "stamps/stamp_list_grouped.html"
    context_object_name = "grouped_qs"
    paginate_by = 10

    def get_queryset(self):
        qs = StampService.get_queryset()
        return StampService.grouped_by_company(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_all_companies"] = StampService.total_amount(
            self.get_queryset()  # full queryset, not paginated
        )

        return context


class StampCreateView(SuccessMessageMixin, CreateView):
    form_class = StampCalculationForm
    template_name = "stamps/add_stamp.html"
    success_url = reverse_lazy("stamp_list")
    success_message = "تمت إضافة حساب الدمغة بنجاح."

    def form_valid(self, form):
        StampService.create_from_form(form)
        return super().form_valid(form)
