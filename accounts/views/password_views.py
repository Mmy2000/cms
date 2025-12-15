from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from accounts.forms import ForgotPasswordForm,ResetPasswordForm
from accounts.services.email_service import EmailService
from accounts.selectors.user_selector import UserSelector
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from accounts.services.user_service import UserService


def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if form.is_valid():
        try:
            user = UserSelector.get_user_by_email(form.cleaned_data["email"])
            UserService.validate_user_for_reset(user)

            token = UserService.generate_token(user)
            EmailService.send_password_reset(request, user, token)

            messages.success(
                request,
                "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.",
            )
            return redirect("login")

        except ValidationError as e:
            messages.error(request, e.message)

    return render(request, "accounts/forgotPassword.html", {"form": form})


def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserSelector.get_by_id(uid)
    except Exception:
        user = None

    if user and UserService.validate_token(user, token):
        request.session["reset_uid"] = uid
        messages.success(request, "يرجى إدخال كلمة مرور جديدة.")
        return redirect("reset_password")

    messages.error(request, "❌ رابط إعادة التعيين غير صالح.")
    return redirect("login")


def reset_password(request):
    form = ResetPasswordForm(request.POST or None)

    if form.is_valid():
        password = form.cleaned_data["new_password"]
        confirm_password = form.cleaned_data["confirm_password"]

        if password != confirm_password:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
            return redirect("reset_password")

        uid = request.session.get("reset_uid")
        user = UserSelector.get_user_by_uid(uid)

        UserService.reset_password(user, password)

        del request.session["reset_uid"]
        messages.success(request, "تم إعادة تعيين كلمة المرور بنجاح.")
        return redirect("login")

    return render(request, "accounts/resetPassword.html", {"form": form})
