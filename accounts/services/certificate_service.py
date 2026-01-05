import io
import os
from datetime import datetime
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display

    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False


class CertificateService:
    """خدمة لتوليد شهادات PDF"""

    # الألوان المستخدمة
    COLORS = {
        "primary": HexColor("#059669"),
        "secondary": HexColor("#10b981"),
        "text": HexColor("#1f2937"),
        "light_text": HexColor("#6b7280"),
        "border": HexColor("#d1d5db"),
    }

    # إعدادات الخطوط
    FONT_SIZES = {
        "title": 26,
        "heading": 18,
        "body": 14,
        "small": 10,
        "table": 10,
    }

    @staticmethod
    def generate_certificate(
        queryset, user, include_qr=False, type="company", include_table=True
    ):
        """
        توليد شهادة PDF

        Args:
            queryset: QuerySet من StampCalculation
            user: المستخدم الحالي
            include_qr: هل يتم إضافة QR code
            type: نوع الشهادة (company أو sector)
            include_table: هل يتم إضافة جدول بالدمغات

        Returns:
            BytesIO: ملف PDF
        """
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # تسجيل الخط
        font_name = CertificateService._register_font()

        # تجهيز البيانات
        if type == "sector":
            data = CertificateService._prepare_expected_stamps_data(queryset, user)
        else:
            data = CertificateService._prepare_stamps_data(queryset, user)

        # رسم الشهادة
        CertificateService._draw_borders(p, width, height)
        y = CertificateService._draw_header(p, width, height, font_name)

        if type == "sector":
            y = CertificateService._draw_expected_stamps_body(
                p, width, y, data, font_name
            )
        else:
            y = CertificateService._draw_stamps_body(p, width, y, data, font_name)

        # إضافة الجدول إذا كان مطلوباً
        if include_table:
            y = CertificateService._draw_stamps_table(
                p, width, y, queryset, font_name, type, data
            )

        # رسم التذييل على آخر صفحة فقط
        CertificateService._draw_footer(p, width, data, font_name)

        # إضافة QR code إذا كان مطلوباً
        if include_qr:
            CertificateService._add_qr_code(p, user.id)

        p.showPage()
        p.save()
        buffer.seek(0)

        return buffer

    @staticmethod
    def _draw_stamps_table(p, width, y, queryset, font_name, type="company", data=None):
        """رسم جدول الدمغات مع دعم التقسيم على صفحات متعددة"""
        colors_def = CertificateService.COLORS
        sizes = CertificateService.FONT_SIZES

        # التحقق من المساحة المتاحة
        min_space_for_table = 200
        if y < min_space_for_table:
            p.showPage()
            CertificateService._draw_borders(p, width, A4[1])
            y = A4[1] - 80

        # عنوان الجدول
        y -= 30
        p.setFont(font_name, sizes["heading"])
        p.setFillColor(colors_def["primary"])
        table_title = CertificateService._arabic("تفاصيل الدمغات المسلمة")
        p.drawCentredString(width / 2, y, table_title)
        y -= 30

        # رأس الجدول
        if type == "sector":
            headers = [
                CertificateService._arabic("تاريخ الإدخال"),
                CertificateService._arabic("القيمة"),
                CertificateService._arabic("السنة"),
                CertificateService._arabic("القطاع"),
                CertificateService._arabic("#"),
            ]
        else:
            headers = [
                CertificateService._arabic("تاريخ الإدخال"),
                CertificateService._arabic("القيمة"),
                CertificateService._arabic("السنة"),
                CertificateService._arabic("الشركة"),
                CertificateService._arabic("#"),
            ]

        # تحضير جميع صفوف البيانات
        all_rows = []
        for idx, stamp in enumerate(queryset.order_by("created_at"), 1):
            if type == "sector":
                entity_name = stamp.sector.name if stamp.sector else "غير محدد"
            else:
                entity_name = stamp.company.name if stamp.company else "غير محدد"

            year = stamp.invoice_date if stamp.invoice_date else "غير محدد"
            value = f"{stamp.d1:,.0f}" if stamp.d1 else "0"
            created = (
                stamp.created_at.strftime("%Y-%m-%d %I:%M %p")
                if stamp.created_at
                else ""
            )

            row = [
                CertificateService._arabic(created),
                CertificateService._arabic(value),
                CertificateService._arabic(str(year)),
                CertificateService._arabic(entity_name[:30]),
                CertificateService._arabic(str(idx)),
            ]
            all_rows.append(row)

        # إعدادات الجدول
        col_widths = [100, 70, 60, 160, 40]
        row_height = 32  # ارتفاع كل صف
        header_height = 44  # ارتفاع رأس الجدول
        footer_space = 150  # المساحة المحجوزة للتذييل

        # حساب عدد الصفوف التي تناسب الصفحة
        rows_per_page = int((y - footer_space - header_height) / row_height)

        # تقسيم الصفوف على صفحات
        total_rows = len(all_rows)
        current_row = 0

        while current_row < total_rows:
            # تحديد الصفوف للصفحة الحالية
            end_row = min(current_row + rows_per_page, total_rows)
            page_rows = all_rows[current_row:end_row]

            # إنشاء بيانات الجدول للصفحة الحالية
            table_data = [headers] + page_rows
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(
                CertificateService._get_table_style(colors_def, sizes, font_name)
            )

            # رسم الجدول
            table_width, table_height = table.wrap(0, 0)
            table_x = (width - table_width) / 2
            table_y = y - table_height

            # التأكد من أن الجدول لن يتداخل مع التذييل
            if table_y < footer_space:
                # إذا كان الجدول سيتداخل، قلل عدد الصفوف
                rows_per_page = max(1, rows_per_page - 1)
                continue

            table.drawOn(p, table_x, table_y)

            current_row = end_row

            # إذا كان هناك المزيد من الصفوف، أنشئ صفحة جديدة
            if current_row < total_rows:
                p.showPage()
                CertificateService._draw_borders(p, width, A4[1])
                y = A4[1] - 80

                # رسم عنوان الجدول للصفحة التالية
                p.setFont(font_name, sizes["heading"])
                p.setFillColor(colors_def["primary"])
                continued_title = CertificateService._arabic(
                    "تفاصيل الدمغات المسلمة (تابع)"
                )
                p.drawCentredString(width / 2, y, continued_title)
                y -= 30

                # إعادة حساب عدد الصفوف للصفحة الجديدة
                rows_per_page = int((y - footer_space - header_height) / row_height)
            else:
                # آخر صفحة - إرجاع الموقع بعد الجدول
                return table_y - 20

        return y

    @staticmethod
    def _get_table_style(colors_def, sizes, font_name):
        """إرجاع تنسيق الجدول"""
        return TableStyle(
            [
                # رأس الجدول
                ("BACKGROUND", (0, 0), (-1, 0), colors_def["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), sizes["table"]),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                # محتوى الجدول
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors_def["text"]),
                ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, -1), font_name),
                ("FONTSIZE", (0, 1), (-1, -1), sizes["table"]),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                # الحدود
                ("GRID", (0, 0), (-1, -1), 1, colors_def["border"]),
                ("BOX", (0, 0), (-1, -1), 2, colors_def["primary"]),
                # صفوف متبادلة
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )

    @staticmethod
    def _register_font():
        """تسجيل الخط العربي"""
        font_dirs = [
            os.path.join(settings.BASE_DIR, "fonts"),
            os.path.join(settings.BASE_DIR, "static", "fonts"),
            "/usr/share/fonts/truetype/dejavu",  # Linux
            "C:/Windows/Fonts",  # Windows
        ]

        font_files = ["Arial.ttf", "DejaVuSans.ttf", "NotoSansArabic-Regular.ttf"]

        for font_dir in font_dirs:
            for font_file in font_files:
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont("Arabic", font_path))
                        return "Arabic"
                    except Exception as e:
                        print(f"خطأ في تحميل الخط {font_path}: {e}")

        return "Helvetica"

    @staticmethod
    def _prepare_stamps_data(queryset, user):
        """تجهيز بيانات الشهادة"""
        user_name = user.get_full_name() or user.username

        # رقم الكارنيه
        card_number = None
        hasattr(user, "profile") and hasattr(user.profile, "syndicate_number")
        card_number = user.profile.syndicate_number

        # الشركات
        companies = list(set(queryset.values_list("company__name", flat=True)))
        companies.sort()  # ترتيب أبجدي

        # السنوات
        years = sorted(
            set(y for y in queryset.values_list("invoice_date__year", flat=True) if y)
        )

        # القيمة الإجمالية
        total_value = sum(s.d1 for s in queryset if s.d1) or 0

        # تاريخ الإدخال
        first_entry = queryset.order_by("created_at").first()

        return {
            "user_name": user_name,
            "card_number": card_number or "غير محدد",
            "companies": companies,
            "companies_count": len(companies),
            "years": years,
            "total_value": total_value,
            "entry_date": (
                first_entry.created_at.strftime("%Y-%m-%d") if first_entry else ""
            ),
            "entry_time": (
                first_entry.created_at.strftime("%H:%M") if first_entry else ""
            ),
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "issue_time": datetime.now().strftime("%H:%M"),
            "cert_id": f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

    @staticmethod
    def _prepare_expected_stamps_data(queryset, user):
        """تجهيز بيانات الشهادة"""
        user_name = user.get_full_name() or user.username

        # رقم الكارنيه
        card_number = None
        hasattr(user, "profile") and hasattr(user.profile, "syndicate_number")
        card_number = user.profile.syndicate_number

        # القطاعات
        sectors = list(set(queryset.values_list("sector__name", flat=True)))
        sectors.sort()  # ترتيب أبجدي

        # السنوات
        years = sorted(
            set(y for y in queryset.values_list("invoice_date__year", flat=True) if y)
        )

        # القيمة الإجمالية
        total_value = sum(s.d1 for s in queryset if s.d1) or 0

        # تاريخ الإدخال
        first_entry = queryset.order_by("created_at").first()

        return {
            "user_name": user_name,
            "card_number": card_number or "غير محدد",
            "sectors": sectors,
            "sectors_count": len(sectors),
            "years": years,
            "total_value": total_value,
            "entry_date": (
                first_entry.created_at.strftime("%Y-%m-%d") if first_entry else ""
            ),
            "entry_time": (
                first_entry.created_at.strftime("%H:%M") if first_entry else ""
            ),
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "issue_time": datetime.now().strftime("%H:%M"),
            "cert_id": f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

    @staticmethod
    def _draw_borders(p, width, height):
        """رسم إطار الشهادة"""
        colors = CertificateService.COLORS

        # إطار خارجي
        p.setStrokeColor(colors["secondary"])
        p.setLineWidth(3)
        p.rect(30, 30, width - 60, height - 60)

        # إطار داخلي
        p.setStrokeColor(colors["primary"])
        p.setLineWidth(1)
        p.rect(40, 40, width - 80, height - 80)

        # زخرفة في الزوايا
        p.setFillColor(colors["secondary"])
        for x, y in [(50, height - 50), (width - 50, height - 50)]:
            p.circle(x, y, 5, fill=1)

    @staticmethod
    def _draw_header(p, width, height, font_name):
        """رسم رأس الشهادة"""
        colors = CertificateService.COLORS
        sizes = CertificateService.FONT_SIZES

        y = height - 100

        # العنوان
        p.setFillColor(colors["primary"])
        p.setFont(font_name, sizes["title"])
        title = CertificateService._arabic("شهادة تسليم بيانات دمغة")
        p.drawCentredString(width / 2, y, title)

        # خط تحت العنوان
        p.setStrokeColor(colors["secondary"])
        p.setLineWidth(2)
        p.line(width / 4, y - 10, 3 * width / 4, y - 10)

        return y - 60

    @staticmethod
    def _draw_stamps_body(p, width, y, data, font_name):
        """رسم محتوى الشهادة"""
        colors = CertificateService.COLORS
        sizes = CertificateService.FONT_SIZES

        p.setFillColor(colors["text"])
        p.setFont(font_name, sizes["body"])

        right_margin = 60
        left_margin = 60
        max_width = width - right_margin - left_margin

        # بناء النص
        lines = [
            f"تشهد إدارة الموقع بأن المهندس: {data['user_name']}",
            f"كارنيه رقم: {data['card_number']}",
            "",
        ]

        # الشركات
        if data["companies_count"] == 1:
            lines.append(
                f"قد سلم بيانات الشركه {data['companies'][0]} عن السنوات الموضحه في الجدول"
            )
        elif data["companies_count"] <= 3:
            companies_text = "، ".join(data["companies"])
            lines.append(f"قد سلم بيانات الشركات عن السنوات الموضحه في الجدول")
        else:
            lines.append(
                f"قد سلم بيانات {data['companies_count']} شركة عن السنوات الموضحه في الجدول"
            )

        lines.extend(
            [
                "",
                f"بقيمة إجمالية: {data['total_value']:,.0f} جنيه مصري",
                f"بأول تاريخ: {data['entry_date']} الساعة: {data['entry_time']}",
                "",
                "ويحتفظ بحقه في الحصول من النقابة عن حافز الدمغة المقرر",
                "عند ورود المبلغ وتسليمه للنقابة.",
                "",
                "وهذه شهادة منا بذلك ولا يحق نشرها على العام.",
            ]
        )

        # طباعة الأسطر
        for line in lines:
            if line:
                text = CertificateService._arabic(line)
                wrapped_lines = simpleSplit(text, font_name, sizes["body"], max_width)
                for wrapped_line in wrapped_lines:
                    p.drawRightString(width - right_margin, y, wrapped_line)
                    y -= 25
            else:
                y -= 25

        return y

    @staticmethod
    def _draw_expected_stamps_body(p, width, y, data, font_name):
        """رسم محتوى الشهادة"""
        colors = CertificateService.COLORS
        sizes = CertificateService.FONT_SIZES

        p.setFillColor(colors["text"])
        p.setFont(font_name, sizes["body"])

        right_margin = 60
        left_margin = 60
        max_width = width - right_margin - left_margin

        # بناء النص
        lines = [
            f"تشهد إدارة الموقع بأن المهندس: {data['user_name']}",
            f"كارنيه رقم: {data['card_number']}",
            "",
        ]

        # القطاعات
        if data["sectors_count"] == 1:
            lines.append(
                f"قد سلم بيانات القطاع {data['sectors'][0]} عن السنوات الموضحه في الجدول"
            )
        elif data["sectors_count"] <= 3:
            sectors_text = "، ".join(data["sectors"])
            lines.append(f"قد سلم بيانات القطاعات عن السنوات الموضحه في الجدول")
        else:
            lines.append(
                f"قد سلم بيانات {data['sectors_count']} قطاع عن السنوات الموضحه في الجدول"
            )

        lines.extend(
            [
                "",
                f"بقيمة إجمالية: {data['total_value']:,.0f} جنيه مصري",
                f"بأول تاريخ: {data['entry_date']} الساعة: {data['entry_time']}",
                "",
                "ويحتفظ بحقه في الحصول من النقابة عن حافز الدمغة المقرر",
                "عند ورود المبلغ وتسليمه للنقابة.",
                "",
                "وهذه شهادة منا بذلك ولا يحق نشرها على العام.",
            ]
        )

        # طباعة الأسطر
        for line in lines:
            if line:
                text = CertificateService._arabic(line)
                wrapped_lines = simpleSplit(text, font_name, sizes["body"], max_width)
                for wrapped_line in wrapped_lines:
                    p.drawRightString(width - right_margin, y, wrapped_line)
                    y -= 25
            else:
                y -= 25

        return y

    @staticmethod
    def _draw_footer(p, width, data, font_name):
        """رسم تذييل الشهادة"""
        colors = CertificateService.COLORS
        sizes = CertificateService.FONT_SIZES

        # خط فاصل
        p.setStrokeColor(colors["border"])
        p.setLineWidth(1)
        p.line(50, 100, width - 50, 100)

        # معلومات الإصدار
        p.setFont(font_name, sizes["small"])
        p.setFillColor(colors["light_text"])

        issue_text = CertificateService._arabic(
            f"تاريخ الإصدار: {data['issue_date']} | الساعة: {data['issue_time']}"
        )
        p.drawCentredString(width / 2, 80, issue_text)

        # الرقم المرجعي
        ref_text = CertificateService._arabic(f"الرقم المرجعي: {data['cert_id']}")
        p.drawCentredString(width / 2, 65, ref_text)

        # ملاحظة
        note_text = CertificateService._arabic(
            "هذه الشهادة صالحة لمدة سنة من تاريخ الإصدار"
        )
        p.setFont(font_name, 8)
        p.drawCentredString(width / 2, 50, note_text)

    @staticmethod
    def _add_qr_code(p, user_id):
        """إضافة QR code للتحقق"""
        BASE_URL = settings.BASE_URL
        verify_url = f"{BASE_URL}/verify/certificate/{user_id}"

        qr_code = qr.QrCodeWidget(verify_url)
        bounds = qr_code.getBounds()
        qr_width = bounds[2] - bounds[0]
        qr_height = bounds[3] - bounds[1]

        d = Drawing(60, 60, transform=[60.0 / qr_width, 0, 0, 60.0 / qr_height, 0, 0])
        d.add(qr_code)
        renderPDF.draw(d, p, 50, 120)

    @staticmethod
    def _arabic(text):
        """تحويل النص العربي لدعم RTL"""
        if ARABIC_SUPPORT:
            try:
                reshaped = reshape(text)
                return get_display(reshaped)
            except:
                pass
        return text
