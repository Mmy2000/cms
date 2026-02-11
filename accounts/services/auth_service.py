from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

class AuthService:
    @staticmethod
    def authenticate_user(request,email: str, password: str):
        user = authenticate(request=request,username=email, password=password)
        if not user:
            raise ValidationError("البريد الإلكتروني أو كلمة المرور غير صحيحة")

        if user.profile.status != "approved":
            raise ValidationError("حسابك قيد المراجعة ولم يتم تفعيله بعد.")

        return user
