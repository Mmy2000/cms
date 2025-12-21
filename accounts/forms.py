from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.utils.translation import gettext_lazy as _


class RegisterForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(label="الاسم الأول")
    last_name = forms.CharField(label="الاسم الأخير")
    email = forms.EmailField(label="البريد الإلكتروني")
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)

    class Meta:
        model = Profile
        fields = ["syndicate_number", "syndicate_card"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "placeholder": f"اكتب {field.label}",
                    "class": "input-style"
                }
            )

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            is_active=False,  # ⛔ Pending
        )

        profile = super().save(commit=False)
        profile.user = user
        profile.status = "pending"

        if commit:
            profile.save()

        return user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("البريد الإلكتروني مستخدم بالفعل.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        password = cleaned_data.get("password")

        if not first_name:
            raise forms.ValidationError("الاسم الأول.يجب أن لا يكون فارغًا.")

        if not last_name:
            raise forms.ValidationError("الاسم الأخير.يجب أن لا يكون فارغًا.")

        if not password:
            raise forms.ValidationError("كلمة المرور.يجب أن لا تكون فارغة.")

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "اكتب بريدك الإلكتروني",
                "class": "input-style"
            },
        ),
    )
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "اكتب كلمة المرور الخاصة بك",
                "class": "input-style"
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email:
            raise forms.ValidationError("البريد الإلكتروني.يجب أن لا يكون فارغًا.")

        if not password:
            raise forms.ValidationError("كلمة المرور.يجب أن لا تكون فارغة.")

        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "اكتب بريدك الإلكتروني",
                "class": "input-style mt-2"
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("لا يوجد مستخدم بهذا البريد الإلكتروني.")
        return email

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "اكتب كلمة المرور الجديدة",
                "class": "input-style mt-2"
            }
        ),
    )
    confirm_password = forms.CharField(
        label="تأكيد كلمة المرور",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "اكتب تأكيد كلمة المرور",
                "class": "input-style mt-2"
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if not new_password:
            raise forms.ValidationError("كلمة المرور الجديدة.يجب أن لا تكون فارغة.")

        if not confirm_password:
            raise forms.ValidationError("تأكيد كلمة المرور.يجب أن لا يكون فارغًا.")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")

        return cleaned_data


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input-style",
                "placeholder": "كلمة المرور الحالية",
            }
        ),
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input-style",
                "placeholder": "كلمة المرور الجديدة",
            }
        ),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input-style",
                "placeholder": "تأكيد كلمة المرور الجديدة",
            }
        ),
    )


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "input-style",
                    "placeholder": "أدخل الاسم الأول",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "input-style",
                    "placeholder": "أدخل الاسم الأخير",
                }
            ),
        }
        labels = {
            "first_name": _("الاسم الأول"),
            "last_name": _("الاسم الأخير"),
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["syndicate_number", "syndicate_card"]
        widgets = {
            "syndicate_number": forms.TextInput(
                attrs={
                    "class": "input-style",
                    "placeholder": "أدخل رقم النقابة",
                }
            ),
            "syndicate_card": forms.FileInput(
                attrs={
                    "class": "hidden",
                    "id": "syndicate_card_input",
                    "accept": "image/*",
                }
            ),
        }
        labels = {
            "syndicate_number": _("رقم النقابة"),
            "syndicate_card": _("كارنيه النقابة"),
        }
