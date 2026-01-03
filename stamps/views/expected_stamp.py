from django.http import HttpResponse
from django.views.generic import ListView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from ..models import  Sector
from ..forms import ExpectedStampForm
from ..services.expected_stamp_service import ExpectedStampService
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncYear
from datetime import  timedelta
from django.utils import timezone
from django.shortcuts import render


class ExpectedStampListView(ListView):
    template_name = "expected_stamps/expected_stamp_list.html"
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

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Handle export
        if request.GET.get("download_btn"):
            file_type = request.GET.get("download")
            sector_id = self.request.GET.get("sector")
            if file_type == "pdf":
                if sector_id not in ["", "None", None]:
                    pdf = ExpectedStampService.export_to_pdf_for_spacific_sector(queryset, sector_id)
                else:
                    pdf = ExpectedStampService.export_pdf(queryset)
                response = HttpResponse(pdf, content_type="application/pdf")
                response["Content-Disposition"] = (
                    "attachment; filename=expected_stamp_report.pdf"
                )
                return response

            elif file_type == "excel":
                excel = ExpectedStampService.export_excel(queryset)
                response = HttpResponse(
                    excel,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = (
                    "attachment; filename=expected_stamp_report.xlsx"
                )
                return response

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        date_to = (self.request.GET.get("date_to"),)
        year = ExpectedStampService.get_last_year(date_to)
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        service = ExpectedStampService()

        context.update(
            {
                "sectors": Sector.objects.all(),
                "sector_filter": self.request.GET.get("sector"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": self.request.GET.get("date_to", ""),
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_sectors": ExpectedStampService.total_amount(qs),
                "total_pension": service.calculate_pension(qs, year),
            }
        )
        return context


class GroupedExpectedStampListView(ListView):
    template_name = "expected_stamps/expected_stamp_list_grouped.html"
    context_object_name = "grouped_qs"
    paginate_by = 10

    def get_queryset(self):
        qs = ExpectedStampService.get_queryset()
        return ExpectedStampService.grouped_by_sector(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_all_sectors"] = ExpectedStampService.total_amount(
            self.get_queryset()  # full queryset, not paginated
        )
        context["total_sectors"] = ExpectedStampService.total_sectors(
            self.get_queryset()  # full queryset, not paginated
        )
        return context

class ExpectedStampDetailView(ListView):
    template_name = "expected_stamps/expected_stamp_details.html"
    context_object_name = "expected_stamps"

    def get_queryset(self):
        stamp_id = self.kwargs.get("stamp_id")
        qs = ExpectedStampService.get_queryset().filter(id=stamp_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        sector_id = qs.first().sector_id if qs.exists() else None
        context["total_amount_for_sector"] = ExpectedStampService.total_amount_for_sector(ExpectedStampService.get_queryset(),sector_id)
        return context

class ExpectedStampCreateView(LoginRequiredMixin,SuccessMessageMixin, CreateView):
    form_class = ExpectedStampForm
    template_name = "expected_stamps/add_expected_stamp.html"
    success_url = reverse_lazy("expected_stamp_list")
    success_message = "تمت إضافة حساب الدمغة المتوقعة بنجاح."

    def form_valid(self, form):
        ExpectedStampService.create_from_form(form, user=self.request.user)
        return super().form_valid(form)


FILTER_MAP = {
    "last_3_year": 3,
    "last_5_years": 5,
    "last_7_years": 7,
    "last_10_years": 10,
}

def expexted_stamp_dashboard(request):

    time_filter = request.GET.get("filter", "all")
    years = FILTER_MAP.get(time_filter)

    # Filter querysets based on date range
    excepted_stamps = ExpectedStampService.get_queryset()
    excepted_stamps = ExpectedStampService.filter_by_years(excepted_stamps, years)

    # Calculate totals
    total_excepted_stamps = ExpectedStampService.total_amount(excepted_stamps)
    chart = ExpectedStampService.yearly_chart(excepted_stamps)

    service = ExpectedStampService()

    context = {
        "total_excepted_stamps": total_excepted_stamps,
        "chart_categories": chart["categories"],
        "excepted_stamp_data": chart["yearly"],
        "total_past_excepted_stamps_data": chart["cumulative"],
        "total_pension": service.calculate_pension(excepted_stamps),
        "current_filter": time_filter,
    }
    return render(request, "expected_stamps/expected_stamp_dashboard.html", context)
