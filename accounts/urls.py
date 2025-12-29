from django.urls import path
from .views.auth_views import GenerateStampCertificateView, MyExpectedStampListView, MyStampListView, register_view, login_view, activate_account,logout,profile_view,edit_profile
from .views.password_views import reset_password , resetpassword_validate , forgot_password,change_password


urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout, name="logout"),
    path("activate/<uidb64>/<token>/", activate_account, name="activate"),
    path("forgot_password/", forgot_password, name="forgot_password"),
    path("reset-password-validate/<uidb64>/<token>/", resetpassword_validate, name="reset_password_validate"),
    path("reset_password/", reset_password, name="reset_password"),    
    path("change_password/", change_password, name="change_password"),    
    path("profile/", profile_view, name="profile"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("my_stamps/", MyStampListView.as_view(), name="my_stamps"),
    path("my_expected_stamps/", MyExpectedStampListView.as_view(), name="my_expected_stamps"),
    path('my_stamps/certificate/', GenerateStampCertificateView.as_view(), name='stamp_certificate'),
]
