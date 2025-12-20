from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError

class UserService:
    @staticmethod
    def activate_user(user: User):
        user.is_active = True
        user.save(update_fields=["is_active"])

    @staticmethod
    def reset_password(user: User, password: str):
        user.set_password(password)
        user.save(update_fields=["password"])

    @staticmethod
    def validate_user_for_reset(user):
        if not user:
            raise ValidationError("لا يوجد مستخدم بهذا البريد الإلكتروني.")

        if user.profile.status != "approved":
            raise ValidationError("لا يمكن إعادة تعيين كلمة المرور لحساب غير مفعل.")

    @staticmethod
    def generate_token(user):
        return default_token_generator.make_token(user)

    @staticmethod
    def validate_token(user, token):
        return default_token_generator.check_token(user, token)

