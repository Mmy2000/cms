from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from ..forms import StampCalculationForm
from ..models import Company
from ..services.stamp_service import StampService
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncYear
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from datetime import datetime


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

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Handle export
        if request.GET.get("download_btn"):
            file_type = request.GET.get("download")
            company_id = request.GET.get("company")

            if file_type == "pdf":
                if company_id not in ["", "None", None]:
                    pdf = StampService.export_to_pdf_for_spacific_company(queryset, company_id)
                else:
                    pdf = StampService.export_pdf(queryset)
                response = HttpResponse(pdf, content_type="application/pdf")
                response["Content-Disposition"] = (
                    "attachment; filename=stamp_report.pdf"
                )
                return response

            elif file_type == "excel":
                excel = StampService.export_excel(queryset)
                response = HttpResponse(
                    excel,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = (
                    "attachment; filename=stamp_report.xlsx"
                )
                return response

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        date_to = (self.request.GET.get("date_to"),)
        year = StampService.get_last_year(date_to)
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        service = StampService()

        context.update(
            {
                "companies": Company.objects.all(),
                "company_filter": self.request.GET.get("company"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": self.request.GET.get("date_to", ""),
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_companies": StampService.total_amount(qs),
                "total_pension": service.calculate_pension(qs,year),
                "30_previous_year": service.get_30_from_previous_year(qs),
            }
        )
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
        context["total_companies"] = StampService.total_companies(
            self.get_queryset()  # full queryset, not paginated
        )

        return context

class StampDetailView( ListView):
    template_name = "stamps/stamp_detail.html"
    context_object_name = "stamps"
    paginate_by = 10

    def get_queryset(self):
        stamp_id = self.kwargs.get("stamp_id")
        qs = StampService.get_queryset().filter(id=stamp_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        company_id = qs.first().company.id if qs.exists() else None
        context["total_amount_for_company"] = StampService.total_amount_for_company(
            StampService.get_queryset(), company_id
        )
        return context

class StampCreateView(LoginRequiredMixin,SuccessMessageMixin, CreateView):
    form_class = StampCalculationForm
    template_name = "stamps/add_stamp.html"
    success_url = reverse_lazy("stamp_list")
    success_message = "تمت إضافة حساب الدمغة بنجاح."

    def form_valid(self, form):
        StampService.create_from_form(form, user=self.request.user)
        return super().form_valid(form)


FILTER_MAP = {
    "last_3_year": 3,
    "last_5_years": 5,
    "last_7_years": 7,
    "last_10_years": 10,
}

def stamp_dashboard(request):
    # Get filter parameter (default to 'all')
    time_filter = request.GET.get("filter", "all")
    years = FILTER_MAP.get(time_filter)

    # Filter querysets based on date range
    stamps = StampService.get_queryset()
    stamps = StampService.filter_by_years(stamps, years)

    # Calculate totals
    total_stamps = StampService.total_amount(stamps)
    chart = StampService.yearly_chart(stamps)
    service = StampService()
    context = {
        "total_stamps": total_stamps,
        "chart_categories": chart["categories"],
        "stamp_data": chart["yearly"],
        "total_past_stamp_data": chart["cumulative"],
        "total_pension": service.calculate_pension(stamps),
        "current_filter": time_filter,
    }

    return render(request, "stamps/stamp_dashboard.html", context)
