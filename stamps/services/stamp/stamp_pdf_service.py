from decimal import Decimal, ROUND_HALF_UP
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from datetime import date
import textwrap
import os
import io
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from django.conf import settings
from num2words import num2words

from stamps.models import Company


class StampPDFService:
    """
    Service for generating PDF exports of stamp calculations.
    Handles both general reports and company-specific detailed reports.
    """

    @staticmethod
    def fix_arabic(text):
        """Convert Arabic text to proper RTL display format."""
        if text is None:
            return ""
        return get_display(reshape(str(text)))

    @staticmethod
    def _number_to_arabic_text(amount) -> str:
        """
        Converts number to Arabic currency text (EGP).
        Supports decimals (piasters).
        """
        amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        pounds = int(amount)
        piasters = int((amount - pounds) * 100)

        parts = []

        if pounds > 0:
            pounds_text = num2words(pounds, lang="ar")
            parts.append(f"{pounds_text} جنيه")

        if piasters > 0:
            piasters_text = num2words(piasters, lang="ar")
            parts.append(f"{piasters_text} قرش")

        if not parts:
            return "صفر جنيه"

        return f"فقط {' و '.join(parts)} لا غير"

    @staticmethod
    def _start_new_page(
        c,
        width,
        height,
        top_margin_cm=7,
        draw_table_header=False,
        headers=None,
        col_widths=None,
    ):
        """Start a new PDF page and reset formatting."""
        TOP_MARGIN = top_margin_cm * cm
        y = height - TOP_MARGIN

        # IMPORTANT: reset font after showPage
        c.setFont("Amiri", 11)

        # Optionally redraw table headers on new page
        if draw_table_header and headers and col_widths:
            LEFT = 2 * cm
            RIGHT = width - 2 * cm

            c.setFont("Amiri-Bold", 11)
            x = RIGHT

            c.line(LEFT, y + 0.4 * cm, RIGHT, y + 0.4 * cm)

            for header, w in zip(headers, col_widths):
                c.drawRightString(x, y, StampPDFService.fix_arabic(header))
                x -= w

            c.line(LEFT, y - 0.3 * cm, RIGHT, y - 0.3 * cm)

            y -= 0.8 * cm
            c.setFont("Amiri", 11)

        return y

    @staticmethod
    def _calculate_total_amount(queryset) -> Decimal:
        """Calculate total d1 amount from queryset."""
        from django.db.models import Sum

        result = queryset.aggregate(total=Sum("d1"))["total"]
        return Decimal(str(result)) if result else Decimal("0")

    @staticmethod
    def export_general_report(queryset):
        """
        Export general PDF report with summary table of all stamps.
        Shows company, date, value, copies, rate, and total.
        """
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

        # Calculate total
        total_amount = StampPDFService._calculate_total_amount(queryset)

        total_paragraph = Paragraph(
            StampPDFService.fix_arabic(
                f"إجمالي الدمغة لكل الشركات بالمليون: {total_amount:,} جنيه مصري"
            ),
            arabic_style,
        )

        # RTL: REVERSED column order
        headers = [
            StampPDFService.fix_arabic("إجمالي الدمغة"),
            StampPDFService.fix_arabic("النسبة"),
            StampPDFService.fix_arabic("عدد النسخ"),
            StampPDFService.fix_arabic("قيمة الأعمال"),
            StampPDFService.fix_arabic("تاريخ المطالبه"),
            StampPDFService.fix_arabic("الشركة"),
        ]

        table_data = [[Paragraph(h, arabic_style) for h in headers]]

        for s in queryset:
            row = [
                Paragraph(f"{s.d1:,}", number_style),
                Paragraph(str(s.stamp_rate), number_style),
                Paragraph(str(s.invoice_copies), number_style),
                Paragraph(f"{s.value_of_work:,}", number_style),
                Paragraph(
                    s.invoice_date.strftime("%Y-%m-%d") if s.invoice_date else "—",
                    number_style,
                ),
                Paragraph(StampPDFService.fix_arabic(s.company.name), arabic_style),
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
    def export_company_detailed_report(queryset, company_id):
        """
        Export detailed PDF report for a specific company.
        Includes legal references, detailed table, and formal footer.
        """
        company = Company.objects.get(id=company_id)
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
        TOP_MARGIN = 7 * cm
        FOOTER_LEFT = 5 * cm
        y = height - TOP_MARGIN

        # ================= Header ================= #
        c.setFont(*HEADER_FONT)
        c.drawRightString(
            FOOTER_LEFT,
            y,
            StampPDFService.fix_arabic(
                f" القاهرة في : {date.today().strftime('%Y-%m-%d')}"
            ),
        )

        c.setFont(*TITLE_FONT)
        c.drawRightString(
            RIGHT, y, StampPDFService.fix_arabic(f"السادة شركة / {company.name}")
        )

        # "تحية طيبة وبعد"
        y -= 1.5 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(width / 2, y, StampPDFService.fix_arabic("تحية طيبة و بعد"))

        # Title
        y -= 1.2 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(
            width / 2, y, StampPDFService.fix_arabic("مطالبة نموذج رقم ( 1 )")
        )

        # ================= Intro paragraph ================= #
        y -= 2 * cm
        c.setFont(*TABLE_HEADER_FONT)

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
            c.drawRightString(RIGHT, y, StampPDFService.fix_arabic(line))
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
            c.drawRightString(x, y, StampPDFService.fix_arabic(header))
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
                c.drawRightString(x, y, StampPDFService.fix_arabic(str(value)))
                x -= w

            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(LEFT, y - 0.2 * cm, RIGHT, y - 0.2 * cm)
            c.setStrokeColorRGB(0, 0, 0)

            y -= ROW_HEIGHT

            # Check if we need a new page
            if y < 4 * cm:
                c.showPage()
                y = StampPDFService._start_new_page(
                    c,
                    width,
                    height,
                    7,
                    draw_table_header=True,
                    headers=headers,
                    col_widths=col_widths,
                )
                c.setFont(*TABLE_ROW_FONT)  # Reset row font after header

        # ================= Total ================= #
        # Check if we have enough space for total section (need ~3cm)
        if y < 5 * cm:
            c.showPage()
            y = StampPDFService._start_new_page(c, width, height, 7)
            c.setFont("Amiri-Bold", 12)

        y -= 0.5 * cm
        c.setFont("Amiri-Bold", 12)

        c.line(LEFT, y + 0.4 * cm, RIGHT, y + 0.4 * cm)

        c.drawRightString(
            RIGHT, y, StampPDFService.fix_arabic(f"الإجمالي : {total:,} جنيه مصري")
        )

        total_in_arabic = StampPDFService.fix_arabic(
            StampPDFService._number_to_arabic_text(total)
        )
        y -= 0.8 * cm
        c.setFont("Amiri-Bold", 12)
        c.drawRightString(RIGHT, y, total_in_arabic)

        # ================= Footer ================= #
        last_points = [
            "١- حق الطعن: يمكنكم الطعن والتقدم بالمستندات خلال خمسة عشر يوماً من تاريخ الاستلام إلى إدارة الدمغة بالنقابة العامة للمهندسين.",
            "٢- المصادقة: يعتبر عدم الاعتراض أو الطعن خلال فترة الـ 15 يوماً المذكورة مصادقة رسمية على المديونية.",
            "٣- التقاعس عن السداد: يتم تطبيق المادة رقم 99 في حالة التقاعس عن الدفع لمدة ثلاثة أشهر.",
        ]

        # Check if we have enough space for footer (need ~8cm for all footer content)
        if y < 10 * cm:
            c.showPage()
            y = StampPDFService._start_new_page(c, width, height, 7)

        y -= 1.6 * cm
        c.setFont(*TABLE_HEADER_FONT)

        for point in last_points:
            c.drawRightString(RIGHT, y, StampPDFService.fix_arabic(point))
            y -= 0.7 * cm

        y -= 1.2 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(
            width / 2, y, StampPDFService.fix_arabic("وتفضلوا بقبول فائق الاحترام")
        )

        y -= 1.3 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(FOOTER_LEFT, y, StampPDFService.fix_arabic("أمين الصندوق"))

        y -= 0.9 * cm
        c.setFont(*TITLE_FONT)
        c.drawCentredString(FOOTER_LEFT, y, StampPDFService.fix_arabic("د / معتز طلبة"))

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer.getvalue()
