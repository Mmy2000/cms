from django.core.exceptions import ValidationError


class PasswordService:
    @staticmethod
    def validate_current_password(user, current_password):
        if not user.check_password(current_password):
            raise ValidationError("كلمة المرور الحالية غير صحيحة.")

    @staticmethod
    def validate_new_password(password, confirm_password):
        if password != confirm_password:
            raise ValidationError("كلمتا المرور غير متطابقتين.")

    @staticmethod
    def change_password(user, new_password):
        user.set_password(new_password)
        user.save(update_fields=["password"])
