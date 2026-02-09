from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.units import cm

from arabic_reshaper import reshape
from bidi.algorithm import get_display
from num2words import num2words


class MainPDFService:

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
                c.drawRightString(x, y, MainPDFService.fix_arabic(header))
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
    def _draw_judicial_seizure_page(c, width, height, user_profile):
        """
        Draw the judicial seizure notice page.
        This is shown when user has judicial_seizure=True.
        """
        LEFT = 2 * cm
        RIGHT = width - 2 * cm
        CENTER = width / 2
        TOP_MARGIN = 3 * cm
        BOTTOM_MARGIN = 2.5 * cm  # Add bottom margin to prevent cutoff
        y = height - TOP_MARGIN
        FOOTER_LEFT = 5 * cm

        # Title at top - BOLD
        c.setFont("Amiri-Bold", 16)
        title = "بمحضر ضبط قضائي لمخالفة مواد (.....................)"
        c.drawCentredString(CENTER, y, MainPDFService.fix_arabic(title))

        y -= 2 * cm

        # Form fields with dotted lines - BOLD
        c.setFont("Amiri-Bold", 12)

        # رقم المسلسل
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic("رقم المسلسل :"))
        c.drawString(LEFT, y, "." * 100)

        y -= 1 * cm

        # رقم القيد بالسجل
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic("رقم القيد بالسجل :"))
        c.drawString(LEFT, y, "." * 100)

        y -= 1 * cm

        # اسم المخالف
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic("اسم المخالف :"))
        c.drawString(LEFT, y, "." * 100)

        y -= 1 * cm

        # عنوان المخالف
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic("عنوان المخالف :"))
        c.drawString(LEFT, y, "." * 100)

        y -= 1.2 * cm

        # انه في يوم ... الموافق
        line1_right = (
            "انه في يوم .............................. الموافق    /    /٢٠٢٥ الساعة :"
        )
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(line1_right))
        c.drawString(LEFT, y, "." * 20)

        y -= 1.2 * cm

        # بمعرفتي انا المحامي
        line2 = "بمعرفتي انا المحامي / ..................................... بصفتي / ......................................."
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(line2))

        y -= 1 * cm

        # محامي بإدارة الدمغة الهندسية
        line3 = "محامي بإدارة الدمغة الهندسية بنقابة المهندسين المصرية ، مأمور الضبط القضائي."
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(line3))

        y -= 1.2 * cm

        # بناء علي قرار السيد وزير العدل - BOLD
        c.setFont("Amiri-Bold", 11)
        para1 = "بناء علي قرار السيد وزير العدل رقم (٤٨٠٥) لسنة ٢٠٢٥ المنشور بالجريدة الرسمية"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(para1))

        y -= 0.7 * cm

        para2 = "بتاريخ ٢٠٢٥/٣/٢٥ العدد (١٨٨) ، فقد تحقق لنا أن السيد – السادة /"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(para2))

        y -= 1 * cm

        c.drawString(LEFT, y, "." * 120)

        y -= 0.7 * cm

        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic("قد قام – قاموا"))
        c.drawString(LEFT, y, "." * 120)

        y -= 1 * cm

        # وبعد التحقيق والتحري - BOLD
        c.setFont("Amiri-Bold", 12)
        investigation = "وبعد التحقيق والتحري عن الأمر بموجب الإجراءات الآتية :"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(investigation))

        y -= 0.8 * cm

        c.setFont("Amiri-Bold", 11)
        c.drawString(LEFT, y, "." * 120)
        y -= 0.7 * cm
        c.drawString(LEFT, y, "." * 120)
        y -= 0.7 * cm
        c.drawString(LEFT, y, "." * 120)

        y -= 1.2 * cm

        # Main paragraph - BOLD
        c.setFont("Amiri-Bold", 11)
        main_text1 = "وحيث أن هذا العمل مخالف للمواد ( ٢٣ ) من قانون الإجراءات الجنائية ومخالفة المواد"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(main_text1))

        y -= 0.7 * cm

        main_text2 = "( ٤٦ - ٤٧ - ١٣١ ) من قانون ٦٦ لسنة ١٩٧٤ ولائحته التنفيذية الصادر بشأن نقابة"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(main_text2))

        y -= 0.7 * cm

        main_text3 = "المهندسين ، نحرر هذا المحضر من أصل وصورتين."
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(main_text3))

        y -= 1.2 * cm

        # Closing - BOLD
        c.setFont("Amiri-Bold", 11)
        closing = "يرسل الأصل إلى النيابة العامة لإتخاذ ما يلزم وطلب الحكم بالعقوبات المقررة قانوناً ، ونسلم صورة"
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(closing))

        y -= 0.7 * cm

        closing2 = "للمخالف وترسل صورة إلى النقابة العامة."
        c.drawRightString(RIGHT, y, MainPDFService.fix_arabic(closing2))

        # Check if we have enough space for signature section (need ~4cm from bottom)
        if y - 4 * cm < BOTTOM_MARGIN:
            c.showPage()
            y = height - TOP_MARGIN
            c.setFont("Amiri-Bold", 12)
        else:
            y -= 1.5 * cm

        # Signature section - BOLD
        c.setFont("Amiri-Bold", 12)
        c.drawCentredString(FOOTER_LEFT, y, MainPDFService.fix_arabic("محرر المحضر"))

        y -= 0.8 * cm

        c.drawCentredString(
            FOOTER_LEFT,
            y,
            MainPDFService.fix_arabic(
                "الاسم : ........................................"
            ),
        )

        y -= 0.8 * cm

        c.drawCentredString(
            FOOTER_LEFT,
            y,
            MainPDFService.fix_arabic(
                "التوقيع : ........................................"
            ),
        )

        y -= 0.8 * cm

        # Ensure we don't go below bottom margin
        if y > BOTTOM_MARGIN:
            c.drawCentredString(
                FOOTER_LEFT,
                y,
                MainPDFService.fix_arabic(
                    "التاريخ : ........................................"
                ),
            )

        # Finish this page
        c.showPage()
