from django.views.generic import ListView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from ..models import  Sector
from ..forms import ExpectedStampForm
from ..services.expected_stamp_service import ExpectedStampService

class ExpectedStampListView(ListView):
    template_name = "expected_stamp_list.html"
    context_object_name = "expected_stamps"
    paginate_by = 10

    def get_queryset(self):
        qs = ExpectedStampService.get_queryset()

        qs = ExpectedStampService.filter(
            qs,
            sector_id=self.request.GET.get("sector"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )

        qs = ExpectedStampService.sort(
            qs,
            self.request.GET.get("sort")
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list

        context.update({
            "sectors": Sector.objects.all(),
            "sector_filter": self.request.GET.get("sector"),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort_by": self.request.GET.get("sort", "-created_at"),
            "total_all_sectors": ExpectedStampService.total_amount(qs),
        })
        return context


class ExpectedStampCreateView(SuccessMessageMixin,CreateView):
    form_class = ExpectedStampForm
    template_name = "add_expected_stamp.html"
    success_url = reverse_lazy("expected_stamp_list")
    success_message = "تمت إضافة حساب الدمغة المتوقعة بنجاح."

    def form_valid(self, form):
        ExpectedStampService.create_from_form(form)
        return super().form_valid(form)
