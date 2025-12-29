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
    }

    @staticmethod
    def generate_certificate(queryset, user, include_qr=False,type="company"):
        """
        توليد شهادة PDF

        Args:
            queryset: QuerySet من StampCalculation
            user: المستخدم الحالي
            include_qr: هل يتم إضافة QR code

        Returns:
            BytesIO: ملف PDF
        """
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # تسجيل الخط
        font_name = CertificateService._register_font()

        # تجهيز البيانات
        if type=="sector":
            data = CertificateService._prepare_expected_stamps_data(queryset, user)
        else:
            data = CertificateService._prepare_stamps_data(queryset, user)

        # رسم الشهادة
        CertificateService._draw_borders(p, width, height)
        y = CertificateService._draw_header(p, width, height, font_name)
        if type=="sector":
            y = CertificateService._draw_expected_stamps_body(p, width, y, data, font_name)
        else:
            y = CertificateService._draw_stamps_body(p, width, y, data, font_name)
        CertificateService._draw_footer(p, width, data, font_name)

        # إضافة QR code إذا كان مطلوباً
        if include_qr:
            CertificateService._add_qr_code(p, user.id)

        p.showPage()
        p.save()
        buffer.seek(0)

        return buffer

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

        # الشركات
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

        # زخرفة في الزوايا (اختياري)
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

        # الشركات (بدون تكرار)
        if data["companies_count"] == 1:
            # شركة واحدة فقط
            lines.append(f"قد سلم بيانات شركة: {data['companies'][0]}")
        elif data["companies_count"] <= 3:
            # 2-3 شركات
            companies_text = "، ".join(data["companies"])
            lines.append(f"قد سلم بيانات شركات: {companies_text}")
        else:
            # أكثر من 3 شركات
            companies_text = "، ".join(data["companies"][:3])
            lines.append(f"قد سلم بيانات شركات: {companies_text}")
            lines.append(f"وشركات أخرى (إجمالي {data['companies_count']} شركة)")

        lines.extend(
            [
                "",
                f"عن سنوات: {', '.join(map(str, data['years']))}",
                f"بقيمة إجمالية: {data['total_value']:,.0f} جنيه مصري",
                f"بتاريخ: {data['entry_date']} الساعة: {data['entry_time']}",
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

                # تقسيم النص إذا كان طويلاً
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

        # الشركات (بدون تكرار)
        if data["sectors_count"] == 1:
            # شركة واحدة فقط
            lines.append(f"قد سلم بيانات قطاع: {data['sectors'][0]}")
        elif data["sectors_count"] <= 3:
            # 2-3 شركات
            sectors_text = "، ".join(data["sectors"])
            lines.append(f"قد سلم بيانات قطاعات: {sectors_text}")
        else:
            # أكثر من 3 شركات
            sectors_text = "، ".join(data["sectors"][:3])
            lines.append(f"قد سلم بيانات قطاعات: {sectors_text}")
            lines.append(f"وقطاعات أخرى (إجمالي {data['sectors_count']} قطاع)")

        lines.extend(
            [
                "",
                f"عن سنوات: {', '.join(map(str, data['years']))}",
                f"بقيمة إجمالية: {data['total_value']:,.0f} جنيه مصري",
                f"بتاريخ: {data['entry_date']} الساعة: {data['entry_time']}",
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
                
                # تقسيم النص إذا كان طويلاً
                wrapped_lines = simpleSplit(text, font_name, sizes['body'], max_width)
                
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
