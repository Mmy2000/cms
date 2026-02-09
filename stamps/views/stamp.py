from django.views.generic import ListView, CreateView,DetailView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse

from stamps.services.stamp.stamp_service import StampService
from ..forms import StampCalculationForm
from ..models import Company
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render


class StampListView(ListView):
    template_name = "stamps/stamp_list.html"
    context_object_name = "stamps"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.service = StampService()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.service.get_queryset()
        qs = self.service.filter(
            qs,
            company_id=self.request.GET.get("company"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )
        qs = self.service.sort(qs, self.request.GET.get("sort"))
        return qs

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.GET.get("download_btn"):
            return self.handle_export(request, self.object_list)
        context = self.get_context_data()
        return self.render_to_response(context)

    def handle_export(self, request, queryset):
        file_type = request.GET.get("download")
        company_id = request.GET.get("company")

        if file_type == "pdf":
            pdf = (
                self.service.export_to_pdf_for_spacific_company(
                    queryset, company_id, user=request.user
                )
                if company_id
                else self.service.export_pdf(queryset)
            )

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=stamp_report.pdf"
            return response

        if file_type == "excel":
            excel = self.service.export_excel_formatted(queryset)
            response = HttpResponse(
                excel,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = "attachment; filename=stamp_report.xlsx"
            return response

    def get_context_data(self, **kwargs):
        date_to = (self.request.GET.get("date_to"),)
        year = self.service.get_last_year(date_to)
        context = super().get_context_data(**kwargs)
        qs = self.object_list

        context.update(
            {
                "companies": Company.objects.all(),
                "company_filter": self.request.GET.get("company"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": date_to or "",
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_companies": self.service.total_amount(qs),
                "total_pension": self.service.calculate_pension(qs, year),
                "30_previous_year": self.service.get_30_from_previous_year(qs),
            }
        )
        return context


class GroupedStampListView(ListView):
    template_name = "stamps/stamp_list_grouped.html"
    context_object_name = "grouped_qs"
    paginate_by = 10

    def get_queryset(self):
        qs = self.service.get_queryset()
        return self.service.grouped_by_company(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = self.object_list  # already evaluated queryset

        context["total_all_companies"] = self.service.total_amount(qs)
        context["total_companies"] = self.service.total_companies(qs)

        return context

    @property
    def service(self):
        return StampService()


class StampDetailView(DetailView):
    template_name = "stamps/stamp_detail.html"
    context_object_name = "stamp"

    @property
    def service(self):
        return StampService()

    def get_object(self):
        stamp_id = self.kwargs.get("stamp_id")
        return self.service.get_stamp_by_id(stamp_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stamp = self.object  # already fetched once
        company_id = stamp.company_id

        qs = self.service.get_queryset()

        context["total_amount_for_company"] = (
            self.service.total_amount_for_company(qs, company_id)
        )

        context["total_invoice_copies_for_company"] = (
            self.service.get_number_of_invoice_copies(qs, company_id)
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
