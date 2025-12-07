from django.db.models import Sum
from django.utils.dateparse import parse_date
from stamps.admin import format_millions
from stamps.models import ExpectedStamp, Sector
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_RIGHT
from io import BytesIO
import os
import openpyxl
from openpyxl.utils import get_column_letter
from arabic_reshaper import reshape
from bidi.algorithm import get_display

class ExpectedStampService:

    @staticmethod
    def get_queryset():
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def filter(queryset, sector_id=None, date_from=None, date_to=None):
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)

        if date_from:
            queryset = queryset.filter(invoice_date__gte=parse_date(date_from))

        if date_to:
            queryset = queryset.filter(invoice_date__lte=parse_date(date_to))

        return queryset

    @staticmethod
    def sort(queryset, sort):
        if sort in ["invoice_date", "-invoice_date"]:
            return queryset.order_by(sort)
        return queryset.order_by("-created_at")

    @staticmethod
    def total_amount(queryset):
        return queryset.aggregate(total=Sum("d1"))["total"] or 0

    @staticmethod
    def total_sectors(queryset):
        return queryset.values("sector__name").distinct().count()

    @staticmethod
    def grouped_by_sector(queryset):
        return (
            queryset.values("sector__name", "stamp_rate")
            .annotate(total=Sum("d1"))
            .order_by("-total")
        )

    @staticmethod
    def create_from_form(form):
        new_sector_name = form.cleaned_data.get("new_sector_name")
        sector = form.cleaned_data.get("sector")

        if new_sector_name:
            sector, _ = Sector.objects.get_or_create(name=new_sector_name)

        expected_stamp = form.save(commit=False)
        expected_stamp.sector = sector
        expected_stamp.save()

        return expected_stamp

    @staticmethod
    def export_pdf(queryset):

        def fix_arabic(text):
            if not text:
                return ""
            return get_display(reshape(text))

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )

        FONT_PATH = os.path.join("static", "fonts", "Amiri-Bold.ttf")
        try:
            pdfmetrics.registerFont(TTFont("Amiri", FONT_PATH))
            font_name = "Amiri"
        except:
            font_name = "Helvetica"

        styles = getSampleStyleSheet()

        arabic_style = ParagraphStyle(
            name="Arabic",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=12,
            alignment=TA_RIGHT,
            leading=14,
        )

        number_style = ParagraphStyle(
            name="Number",
            parent=arabic_style,
            alignment=TA_RIGHT,
        )

        # ----------- NEW: Calculate TOTAL -----------
        total_amount = ExpectedStampService.total_amount(queryset)

        total_paragraph = Paragraph(
            fix_arabic(
                f"إجمالي الدمغة لكل القطاعات بالمليون: {format_millions(total_amount)}"
            ),
            arabic_style,
        )
        # --------------------------------------------

        # RTL: REVERSED column order
        headers = [
            fix_arabic("إجمالي الدمغة"),
            fix_arabic("النسبة"),
            fix_arabic("عدد النسخ"),
            fix_arabic("قيمة الأعمال"),
            fix_arabic("تاريخ المطالبه"),
            fix_arabic("القطاع"),
        ]

        table_data = [[Paragraph(h, arabic_style) for h in headers]]

        for s in queryset:
            row = [
                Paragraph(format_millions(s.d1), number_style),
                Paragraph(str(s.stamp_rate), number_style),
                Paragraph(str(s.invoice_copies), number_style),
                Paragraph(format_millions(s.value_of_work), number_style),
                Paragraph(
                    s.invoice_date.strftime("%Y-%m-%d") if s.invoice_date else "—",
                    number_style,
                ),
                Paragraph(fix_arabic(s.sector.name), arabic_style),
            ]

            table_data.append(row)

        table = Table(
            table_data,
            colWidths=[95, 60, 60, 90, 80, 120],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgreen),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        # Build PDF with total on top
        doc.build([total_paragraph, Spacer(1, 12), table])

        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    @staticmethod
    def export_excel(queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Stamp Report"

        headers = [
            "القطاع",
            "تاريخ المطالبه",
            "قيمة الأعمال",
            "عدد النسخ",
            "النسبة",
            "إجمالي الدمغة",
        ]
        ws.append(headers)

        for s in queryset:
            ws.append(
                [
                    s.sector.name,
                    s.invoice_date.strftime("%Y-%m-%d") if s.invoice_date else "—",
                    s.value_of_work,
                    s.invoice_copies,
                    s.stamp_rate,
                    s.d1,
                ]
            )

        # Adjust column width
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 20

        output = BytesIO()
        wb.save(output)
        return output.getvalue()
