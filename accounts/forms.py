from django import forms
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(label="الاسم الأول")
    last_name = forms.CharField(label="الاسم الأخير")
    email = forms.EmailField()
    password = forms.CharField()

    class Meta:
        model = Profile
        fields = ["syndicate_number", "syndicate_card"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition"
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
                "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition"
            }
        ),
    )
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition"
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
