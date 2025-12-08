from django.urls import path
from .views import register_view, login_view, activate_account, logout, forgotPassword,resetpassword_validate,resetPassword

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout, name="logout"),
    path("activate/<uidb64>/<token>/", activate_account, name="activate"),
    path("forgot_password/", forgotPassword, name="forgot_password"),
    path("reset-password-validate/<uidb64>/<token>/", resetpassword_validate, name="reset_password_validate"),
    path("reset_password/", resetPassword, name="reset_password"),
]
