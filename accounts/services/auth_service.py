from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

class AuthService:
    @staticmethod
    def authenticate_user(email: str, password: str):
        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError("البريد الإلكتروني أو كلمة المرور غير صحيحة")

        if user.profile.status != "approved":
            raise ValidationError("حسابك قيد المراجعة ولم يتم تفعيله بعد.")

        return user

