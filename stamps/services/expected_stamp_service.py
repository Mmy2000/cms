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
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from bidi.algorithm import get_display
from django.conf import settings
import io
from datetime import date
import textwrap

class ExpectedStampService:

    @staticmethod
    def get_queryset():
        return ExpectedStamp.objects.select_related("sector")

    @staticmethod
    def filter(queryset, sector_id=None, date_from=None, date_to=None):
        if sector_id not in [None, "", "None"]:
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
    def total_amount_for_sector(queryset, sector_id):
        return queryset.filter(sector_id=sector_id).aggregate(total=Sum("d1"))["total"] or 0

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
    def fix_arabic(text):
        if not text:
            return ""
        return get_display(reshape(str(text)))

    @staticmethod
    def export_pdf(queryset):

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
            ExpectedStampService.fix_arabic(
                f"إجمالي الدمغة لكل القطاعات بالمليون: {format_millions(total_amount)}"
            ),
            arabic_style,
        )
        # --------------------------------------------

        # RTL: REVERSED column order
        headers = [
            ExpectedStampService.fix_arabic("إجمالي الدمغة"),
            ExpectedStampService.fix_arabic("النسبة"),
            ExpectedStampService.fix_arabic("عدد النسخ"),
            ExpectedStampService.fix_arabic("قيمة الأعمال"),
            ExpectedStampService.fix_arabic("تاريخ المطالبه"),
            ExpectedStampService.fix_arabic("القطاع"),
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
                Paragraph(ExpectedStampService.fix_arabic(s.sector.name), arabic_style),
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
    def export_to_pdf_for_spacific_sector(queryset, sector_id):

        company = Sector.objects.get(id=sector_id)
        buffer = io.BytesIO()

        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ================= Fonts ================= #
        pdfmetrics.registerFont(
            TTFont("Amiri", settings.BASE_DIR / "static/fonts/Amiri-Regular.ttf")
        )
        pdfmetrics.registerFont(
            TTFont("Amiri-Bold", settings.BASE_DIR / "static/fonts/Amiri-Bold.ttf")
        )

        # ================= Layout constants ================= #
        HEADER_FONT = ("Amiri", 12)
        TITLE_FONT = ("Amiri-Bold", 14)
        PARA_FONT = ("Amiri", 11)
        TABLE_HEADER_FONT = ("Amiri-Bold", 11)
        TABLE_ROW_FONT = ("Amiri", 11)

        LINE_HEIGHT = 0.8 * cm
        ROW_HEIGHT = 0.7 * cm
        LEFT = 2 * cm
        RIGHT = width - 2 * cm

        y = height - 2 * cm

        # ================= Header ================= #
        c.setFont(*HEADER_FONT)
        c.drawRightString(
            RIGHT,
            y,
            ExpectedStampService.fix_arabic(
                f"القاهرة في : {date.today().strftime('%Y-%m-%d')}"
            ),
        )

        y -= 1.2 * cm
        c.drawRightString(
            RIGHT, y, ExpectedStampService.fix_arabic(f"السادة قطاع / {company.name}")
        )

        # "تحية طيبة وبعد"
        y -= 1.5 * cm
        c.setFont("Amiri-Bold", 13)
        c.drawCentredString(width / 2, y, ExpectedStampService.fix_arabic("تحية طيبة و بعد"))

        # Title
        y -= 1.2 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(
            width / 2, y, ExpectedStampService.fix_arabic("مطالبة نموذج رقم ( 1 )")
        )

        # ================= Intro paragraph ================= #
        y -= 2 * cm
        c.setFont(*PARA_FONT)

        paragraph_text = (
            "بمراجعة حجم اعمالكم وجد لديكم كدمغة هندسية لم تورد طبقا للقانون رقم 66 لسنة 1974 "
            "و مواد الدمغة ارقام 45&46&47&48&99 و مواد اللائحة التنفيذية ارقام 130&131&132&149 "
            "وحكم الدستورية في الدعوي رقم 16 لسنة 38 ق دستورية في 5-12-2020. "
            "وحكم جنح مستانف سمالوط رقم 206لسنة 2018"
        )

        # WRAP paragraph across full width (RIGHT → LEFT)
        max_width = RIGHT - LEFT
        wrapped_lines = textwrap.wrap(paragraph_text, width=85)

        for line in wrapped_lines:
            c.drawRightString(RIGHT, y, ExpectedStampService.fix_arabic(line))
            y -= 0.7 * cm

        # ================= Table ================= #
        y -= 1.2 * cm

        headers = [
            "التاريخ",
            "حجم الأعمال",
            "الدمغة الهندسية",
            "عدد النسخ",
            "إجمالي الدمغة",
        ]

        col_widths = [
            3 * cm,
            4 * cm,
            3.5 * cm,
            3 * cm,
            4.5 * cm,
        ]

        c.setFont(*TABLE_HEADER_FONT)
        x = RIGHT

        c.line(LEFT, y + 0.4 * cm, RIGHT, y + 0.4 * cm)

        for header, w in zip(headers, col_widths):
            c.drawRightString(x, y, ExpectedStampService.fix_arabic(header))
            x -= w

        c.line(LEFT, y - 0.3 * cm, RIGHT, y - 0.3 * cm)

        y -= LINE_HEIGHT

        # ---------- Table rows ---------- #
        total = 0
        c.setFont(*TABLE_ROW_FONT)

        for obj in queryset:
            x = RIGHT

            row = [
                obj.invoice_date.strftime("%Y-%m-%d") if obj.invoice_date else "—",
                f"{obj.value_of_work:,}",
                f"{obj.stamp_rate}",
                obj.invoice_copies,
                f"{obj.d1:,}",
            ]

            total += obj.d1

            for value, w in zip(row, col_widths):
                c.drawRightString(x, y, ExpectedStampService.fix_arabic(str(value)))
                x -= w

            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(LEFT, y - 0.2 * cm, RIGHT, y - 0.2 * cm)
            c.setStrokeColorRGB(0, 0, 0)

            y -= ROW_HEIGHT

            if y < 4 * cm:
                c.showPage()
                c.setFont(*TABLE_ROW_FONT)
                y = height - 2 * cm

        # ================= Total ================= #
        y -= 0.5 * cm
        c.setFont("Amiri-Bold", 12)

        c.line(LEFT, y + 0.4 * cm, RIGHT, y + 0.4 * cm)

        c.drawRightString(
            RIGHT, y, ExpectedStampService.fix_arabic(f"الإجمالي : {total:,} جنيه مصري")
        )

        # ================= Footer ================= #
        last_points = [
            "١- في الاعتراض التقدم بمستنداتكم خلال شهر لإدارة الدمغة بنقابة المهندسين.",
            "٢- عدم الاعتراض أو الطعن خلال ١٥ يوم يعتبر مصادقة علي المديونية.",
            "٣- تطبق المادة ٩٩ عند التقاعس مدة ثلاث شهور عن الدفع.",
        ]

        y -= 1.6 * cm
        c.setFont("Amiri", 10)

        for point in last_points:
            c.drawRightString(RIGHT, y, ExpectedStampService.fix_arabic(point))
            y -= 0.7 * cm  # المسافة بين النقاط

        y -= 1.2 * cm
        c.setFont("Amiri", 11)
        c.drawRightString(
            RIGHT, y, ExpectedStampService.fix_arabic("وتفضلوا بقبول فائق الاحترام")
        )

        y -= 1.3 * cm
        c.setFont("Amiri-Bold", 11)
        c.drawRightString(RIGHT, y, ExpectedStampService.fix_arabic("أمين الصندوق"))

        y -= 0.9 * cm
        c.drawRightString(RIGHT, y, ExpectedStampService.fix_arabic("د / معتز طلبة"))

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer.getvalue()

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
