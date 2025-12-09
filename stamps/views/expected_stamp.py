from django.http import HttpResponse
from django.views.generic import ListView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from ..models import  Sector
from ..forms import ExpectedStampForm
from ..services.expected_stamp_service import ExpectedStampService
from django.contrib.auth.mixins import LoginRequiredMixin


class ExpectedStampListView(LoginRequiredMixin,ListView):
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


class GroupedExpectedStampListView(LoginRequiredMixin,ListView):
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


class ExpectedStampCreateView(LoginRequiredMixin,SuccessMessageMixin, CreateView):
    form_class = ExpectedStampForm
    template_name = "expected_stamps/add_expected_stamp.html"
    success_url = reverse_lazy("expected_stamp_list")
    success_message = "تمت إضافة حساب الدمغة المتوقعة بنجاح."

    def form_valid(self, form):
        ExpectedStampService.create_from_form(form)
        return super().form_valid(form)
