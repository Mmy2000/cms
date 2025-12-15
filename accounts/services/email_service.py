from ..utils import send_activation_email, send_reset_password_email


class EmailService:
    @staticmethod
    def send_activation(request, user):
        send_activation_email(request, user)

    @staticmethod
    def send_password_reset(request, user, token):
        send_reset_password_email(request, user, token)
