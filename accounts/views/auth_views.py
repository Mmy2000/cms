from django.shortcuts import render, redirect
from django.contrib import messages,auth
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from accounts.decorators import anonymous_required
from accounts.forms import ProfileEditForm, RegisterForm, LoginForm, UserEditForm
from accounts.services.profile_sevice import ProfileService
from accounts.services.user_service import UserService
from accounts.services.auth_service import AuthService
from accounts.services.email_service import EmailService
from accounts.selectors.user_selector import UserSelector
from accounts.tokens import account_activation_token
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _


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
