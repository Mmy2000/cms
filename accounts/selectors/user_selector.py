from django.contrib.auth.models import User


class UserSelector:
    @staticmethod
    def get_user_by_uid(uid):
        return User.objects.filter(pk=uid).first()

    @staticmethod
    def get_user_by_email(email):
        return User.objects.filter(email=email).first()
