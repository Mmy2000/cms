import os
from django.shortcuts import render, redirect
from django.contrib import messages,auth
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from accounts.decorators import anonymous_required
from accounts.forms import ProfileEditForm, RegisterForm, LoginForm, UserEditForm
from accounts.services.certificate_service import CertificateService
from accounts.services.profile_sevice import ProfileService
from accounts.services.user_service import UserService
from accounts.services.auth_service import AuthService
from accounts.services.email_service import EmailService
from accounts.selectors.user_selector import UserSelector
from accounts.tokens import account_activation_token
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from stamps.models import Company, ExpectedStamp, Sector, StampCalculation
from stamps.services.expected_stamp.expected_stamp_service import ExpectedStampService
from django.http import FileResponse, HttpResponse
from django.views import View
from datetime import datetime

from stamps.services.stamp.stamp_service import StampService


@anonymous_required(path_url="main_topics")
def register_view(request):
    form = RegisterForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        user = form.save()
        EmailService.send_activation(request, user)

        messages.success(
            request,
            "تم إنشاء الحساب بنجاح. تم إرسال رابط التفعيل إلى بريدك الإلكتروني.",
        )
        return redirect("login")

    return render(request, "accounts/register.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserSelector.get_user_by_uid(uid)
    except Exception:
        user = None

    if user and account_activation_token.check_token(user, token):
        UserService.activate_user(user)
        messages.success(request, "تم تفعيل حسابك بنجاح.")
        return redirect("login")

    messages.error(request, "❌ رابط التفعيل غير صالح.")
    return redirect("register")


@anonymous_required(path_url="main_topics")
def login_view(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        try:
            user = AuthService.authenticate_user(
                form.cleaned_data["email"],
                form.cleaned_data["password"],
            )
            login(request, user)
            return redirect("main_topics")

        except ValidationError as e:
            messages.error(request, e.message)

    return render(request, "accounts/login.html", {"form": form})


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("login")

@login_required(login_url="login")
def profile_view(request):
    profile = ProfileService.get_profile(request.user)
    return render(request, "profile/profile.html", {"profile": profile})


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _("تم تحديث الملف الشخصي بنجاح"))
            return redirect("profile")
        else:
            messages.error(request, _("يرجى تصحيح الأخطاء أدناه"))
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    }
    return render(request, "profile/edit_profile.html", context)


class MyStampListView(LoginRequiredMixin, ListView):
    model = StampCalculation
    template_name = "stamps/my_stamps.html"
    context_object_name = "stamps"
    paginate_by = 10

    def get_queryset(self):
        qs = StampService.get_queryset()

        qs = StampService.filter(
            qs,
            company_id=self.request.GET.get("company"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
            user=self.request.user,
        )

        qs = StampService.sort(qs, self.request.GET.get("sort"))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        context.update(
            {
                "companies": Company.objects.filter(
                    stamp_calculations__user=self.request.user
                ).distinct(),
                "company_filter": self.request.GET.get("company"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": self.request.GET.get("date_to", ""),
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_companies": StampService.total_amount(qs),
            }
        )
        return context

class MyExpectedStampListView(LoginRequiredMixin, ListView):
    model = ExpectedStamp
    template_name = "stamps/my_expected_stamps.html"
    context_object_name = "expected_stamps"
    paginate_by = 10

    def get_queryset(self):
        qs = ExpectedStampService.get_queryset()

        qs = ExpectedStampService.filter(
            qs,
            sector_id=self.request.GET.get("sector"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
            user=self.request.user,
        )

        qs = ExpectedStampService.sort(qs, self.request.GET.get("sort"))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        context.update(
            {
                "sectors": Sector.objects.all(),
                "sector_filter": self.request.GET.get("sector"),
                "date_from": self.request.GET.get("date_from", ""),
                "date_to": self.request.GET.get("date_to", ""),
                "sort_by": self.request.GET.get("sort", "-created_at"),
                "total_all_sectors": ExpectedStampService.total_amount(qs),
            }
        )
        return context

class GenerateStampCertificateView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        # الحصول على البيانات المفلترة
        if request.GET.get("type") == "sector":
            qs = self.get_filtered__expected_stamps_queryset()
        else:
            qs = self.get_filtered_stamps_queryset()

        # التحقق من وجود بيانات
        if not qs.exists():
            return self._no_data_response()

        # توليد الشهادة
        try:
            # include_qr=True إذا أردت إضافة QR code
            buffer = CertificateService.generate_certificate(
                queryset=qs, user=request.user, include_qr=False,type=request.GET.get("type"),include_table=True
            )

            # إرجاع الملف
            filename = (
                f'stamp_certificate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
            return FileResponse(buffer, as_attachment=True, filename=filename)

        except Exception as e:
            # في حالة حدوث خطأ
            return HttpResponse(
                f'<html><body style="font-family: Arial; text-align: center; padding: 50px;">'
                f"<h1>⚠️ خطأ</h1>"
                f'<p style="font-size: 18px;">حدث خطأ أثناء إنشاء الشهادة</p>'
                f'<p style="color: #dc2626;">{str(e)}</p>'
                f'<p><a href="javascript:history.back()" style="color: #3b82f6;">← العودة</a></p>'
                f"</body></html>",
                status=500,
            )

    def get_filtered_stamps_queryset(self):
        """الحصول على المطالبات المفلترة بنفس معايير صفحة القائمة"""
        qs = StampService.get_queryset()

        qs = StampService.filter(
            qs,
            company_id=self.request.GET.get("company"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
            user=self.request.user,
        )

        qs = StampService.sort(qs, self.request.GET.get("sort"))

        return qs
    
    def get_filtered__expected_stamps_queryset(self):
        """الحصول على المطالبات المتوقعة المفلترة بنفس معايير صفحة القائمة"""
        qs = ExpectedStampService.get_queryset()

        qs = ExpectedStampService.filter(
            qs,
            sector_id=self.request.GET.get("sector"),
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
            user=self.request.user,
        )

        qs = ExpectedStampService.sort(qs, self.request.GET.get("sort"))

        return qs

    def _no_data_response(self):
        """رسالة في حالة عدم وجود بيانات"""
        return HttpResponse(
            '<html><body style="font-family: Arial; text-align: center; padding: 50px; direction: rtl;">'
            '<div style="max-width: 600px; margin: 0 auto;">'
            '<div style="font-size: 64px; margin-bottom: 20px;">📭</div>'
            '<h1 style="color: #374151;">لا توجد بيانات</h1>'
            '<p style="font-size: 18px; color: #6b7280; margin: 20px 0;">'
            "لا توجد بيانات لطباعة الشهادة. يرجى التأكد من وجود سجلات دمغة مطابقة للفلاتر المحددة."
            "</p>"
            '<a href="javascript:history.back()" '
            'style="display: inline-block; padding: 12px 24px; background: #3b82f6; '
            'color: white; text-decoration: none; border-radius: 8px; margin-top: 20px;">'
            "← العودة للقائمة"
            "</a>"
            "</div>"
            "</body></html>",
            status=400,
        )
