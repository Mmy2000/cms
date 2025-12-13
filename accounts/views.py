from django.shortcuts import render, redirect
from django.contrib import messages, auth

from .utils import send_activation_email, send_reset_password_email
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .tokens import account_activation_token
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "✅ تم تفعيل حسابك بنجاح، يمكنك تسجيل الدخول الآن.")
        return redirect("login")
    else:
        messages.error(request, "❌ رابط التفعيل غير صالح.")
        return redirect("register")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()

            send_activation_email(request, user)

            messages.success(
                request,
                "✅ تم إنشاء الحساب بنجاح. تم إرسال رابط التفعيل إلى بريدك الإلكتروني.",
            )
            return redirect("login")

        else:
            messages.error(request, "من فضلك صحح الأخطاء بالأسفل")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=email, password=password)

            if user:
                if user.profile.status != "approved":
                    messages.error(request, "حسابك قيد المراجعة ولم يتم تفعيله بعد.")
                else:
                    login(request, user)
                    return redirect("main_topics")
            else:
                messages.error(request, "البريد الإلكتروني أو كلمة المرور غير صحيحة")

    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})

@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("login")


def forgotPassword(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
                if user.profile.status != "approved":
                    messages.error(
                        request,
                        "لا يمكن إعادة تعيين كلمة المرور لحساب غير مفعل.",
                    )
                    return redirect("forgot_password")
                token = default_token_generator.make_token(user)
                send_reset_password_email(request, user, token)
                messages.success(
                    request,
                    "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.",
                )
                return redirect("login")
            except User.DoesNotExist:
                messages.error(request, "لا يوجد مستخدم بهذا البريد الإلكتروني.")
    else:
        form = ForgotPasswordForm()
    return render(request, "accounts/forgotPassword.html", {"form": form})


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "يرجى إعادة تعيين كلمة المرور الخاصة بك.")
        return redirect("reset_password")
    else:
        messages.error(request, "❌ رابط التفعيل غير صالح.")
        return redirect("login")

def resetPassword(request):
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["new_password"]
            confirm_password = form.cleaned_data["confirm_password"]

            if password == confirm_password:
                uid = request.session.get("uid")
                user = User.objects.get(pk=uid)
                user.set_password(password)
                user.save()
                messages.success(request, "تم إعادة تعيين كلمة المرور بنجاح.")
                return redirect("login")
            else:
                messages.error(request, "كلمتا المرور غير متطابقتين.")
    else:
        form = ResetPasswordForm()
    return render(request, "accounts/resetPassword.html", {"form": form})
