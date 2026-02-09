from django.http import HttpResponse
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from stamps.services.expected_stamp.expected_stamp_service import ExpectedStampService
from ..models import  Sector
from ..forms import ExpectedStampForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render


class ExpectedStampListView(ListView):
    template_name = "expected_stamps/expected_stamp_list.html"
    context_object_name = "expected_stamps"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.service = ExpectedStampService()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.service.get_queryset()
        qs = self.service.filter(
            qs,
            sector_id=self.request.GET.get("sector"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )
        qs = self.service.sort(
            qs,
            self.request.GET.get("sort")
        )
        return qs

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.GET.get("download_btn"):
            return self.handle_export(request, self.object_list)
        context = self.get_context_data()
        return self.render_to_response(context)

    def handle_export(self, request, queryset):
        file_type = request.GET.get("download")
        sector_id = self.request.GET.get("sector")
        if file_type == "pdf":
            pdf = (
                self.service.export_to_pdf_for_spacific_sector(
                    queryset, sector_id, user=request.user
                )
                if sector_id
                else self.service.export_pdf(queryset)
            )
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                "attachment; filename=expected_stamp_report.pdf"
            )
            return response

        elif file_type == "excel":
            excel = self.service.export_excel_formatted(queryset)
            response = HttpResponse(
                excel,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                "attachment; filename=expected_stamp_report.xlsx"
            )
            return response

    def get_context_data(self, **kwargs):
        date_to = (self.request.GET.get("date_to"),)
        year = self.service.get_last_year(date_to)
        context = super().get_context_data(**kwargs)
        qs = self.object_list

        context.update(
            {
                "sectors": Sector.objects.all(),
                "sector_filter": self.request.GET.get("sector"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": date_to or "",
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_sectors": self.service.total_amount(qs),
                "total_pension": self.service.calculate_pension(qs, year),
                "30_previous_year": self.service.get_30_from_previous_year(qs),
            }
        )
        return context


class GroupedExpectedStampListView(ListView):
    template_name = "expected_stamps/expected_stamp_list_grouped.html"
    context_object_name = "grouped_qs"
    paginate_by = 10

    @property
    def service(self):
        return ExpectedStampService()

    def get_queryset(self):
        qs = self.service.get_queryset()
        return self.service.grouped_by_sector(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list

        context["total_all_sectors"] = self.service.total_amount(
            qs  # full queryset, not paginated
        )
        context["total_sectors"] = self.service.total_sectors(
            qs  # full queryset, not paginated
        )
        return context

class ExpectedStampDetailView(DetailView):
    template_name = "expected_stamps/expected_stamp_details.html"
    context_object_name = "stamp"

    @property
    def service(self):
        return ExpectedStampService()

    def get_object(self):
        stamp_id = self.kwargs.get("stamp_id")
        return self.service.get_expected_stamp_by_id(stamp_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stamp = self.object
        sector_id = stamp.sector_id
        qs = self.service.get_queryset()
        context["total_amount_for_sector"] = self.service.total_amount_for_sector(qs,sector_id)
        context["total_invoice_copies_for_sector"] = self.service.get_number_of_invoice_copies(
            qs, sector_id
        )
        return context

class ExpectedStampCreateView(LoginRequiredMixin,SuccessMessageMixin, CreateView):
    form_class = ExpectedStampForm
    template_name = "expected_stamps/add_expected_stamp.html"
    success_url = reverse_lazy("expected_stamp_list")
    success_message = "تمت إضافة حساب الدمغة المتوقعة بنجاح."

    def form_valid(self, form):
        ExpectedStampService.create_from_form(form, user=self.request.user)
        return super().form_valid(form)


class ExpectedStampDashboardView(TemplateView):
    template_name = "expected_stamps/expected_stamp_dashboard.html"

    FILTER_MAP = {
        "last_3_year": 3,
        "last_5_years": 5,
        "last_7_years": 7,
        "last_10_years": 10,
    }

    def dispatch(self, request, *args, **kwargs):
        self.service = ExpectedStampService()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        time_filter = self.request.GET.get("filter", "all")
        years = None if time_filter == "all" else self.FILTER_MAP.get(time_filter)

        excepted_stamps =  self.service.filter_by_years(self.service.get_queryset(), years)

        chart = self.service.yearly_chart(excepted_stamps)

        context = {
            "total_excepted_stamps": self.service.total_amount(excepted_stamps),
            "chart_categories": chart["categories"],
            "excepted_stamp_data": chart["yearly"],
            "total_past_excepted_stamps_data": chart["cumulative"],
            "total_pension": self.service.calculate_pension(excepted_stamps),
            "current_filter": time_filter,
        }

        return context
