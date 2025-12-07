from django.urls import path
from .views import register_view, login_view, activate_account, logout

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout, name="logout"),
    path("activate/<uidb64>/<token>/", activate_account, name="activate"),
]
