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


# class RegisterForm(forms.ModelForm):
#     # User fields
#     first_name = forms.CharField(
#         label="الاسم الأول",
#         widget=forms.TextInput(
#             attrs={
#                 "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                 "placeholder": "الاسم الأول",
#             }
#         ),
#     )
#     last_name = forms.CharField(
#         label="الاسم الأخير",
#         widget=forms.TextInput(
#             attrs={
#                 "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                 "placeholder": "الاسم الأخير",
#             }
#         ),
#     )
#     email = forms.EmailField(
#         widget=forms.EmailInput(
#             attrs={
#                 "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                 "placeholder": "البريد الإلكتروني",
#             }
#         )
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(
#             attrs={
#                 "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                 "placeholder": "كلمة المرور",
#             }
#         )
#     )

#     class Meta:
#         model = Profile
#         fields = ["syndicate_number", "syndicate_card"]

#         widgets = {
#             "syndicate_number": forms.TextInput(
#                 attrs={
#                     "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                     "placeholder": "رقم النقابة",
#                 }
#             ),
#             "syndicate_card": forms.ClearableFileInput(
#                 attrs={
#                     "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
#                 }
#             ),
#         }

#     def save(self, commit=True):
#         user = User.objects.create_user(
#             username=self.cleaned_data["email"],
#             email=self.cleaned_data["email"],
#             password=self.cleaned_data["password"],
#             first_name=self.cleaned_data["first_name"],
#             last_name=self.cleaned_data["last_name"],
#             is_active=False,  # ⛔ Pending
#         )

#         profile = super().save(commit=False)
#         profile.user = user
#         profile.status = "pending"

#         if commit:
#             profile.save()

#         return user
