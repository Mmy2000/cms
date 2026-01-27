from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from stamps.tasks import send_email
from .tokens import account_activation_token


def send_activation_email(request, user):
    current_site = get_current_site(request)

    mail_subject = "تفعيل حسابك"
    message = render_to_string(
        "accounts/email_activation.html",
        {
            "user": user,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    send_email.enqueue(
        to_email=user.email,
        first_name=user.first_name,
        subject=mail_subject,
        message=message,
    )

def send_reset_password_email(request, user, token):
    current_site = get_current_site(request)

    mail_subject = "إعادة تعيين كلمة المرور"
    message = render_to_string(
        "accounts/email_reset_password.html",
        {
            "user": user,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token,
        },
    )
    send_email.enqueue(
        to_email=user.email,
        first_name=user.first_name,
        subject=mail_subject,
        message=message,
    )
