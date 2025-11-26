from django import forms
from .models import StampCalculation


class StampCalculationForm(forms.ModelForm):

    new_company_name = forms.CharField(
        label="اسم شركة جديدة",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "اكتب اسم الشركة إذا لم تكن موجودة",
                "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition"
            }
        ),
    )

    class Meta:
        model = StampCalculation
        fields = [
            "company",
            "value_of_work",
            "invoice_copies",
            "invoice_date",
            "stamp_rate",
            "exchange_rate",
            "note",
        ]

        widgets = {
            "company": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition"
                }
            ),
            "value_of_work": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg "
                    "focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "قيمة العمل",
                }
            ),
            "invoice_copies": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg "
                    "focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "عدد النسخ",
                }
            ),
            "invoice_date": forms.DateInput(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg "
                    "focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "سنة الفاتورة",
                    "type": "date",  # Enables date picker
                }
            ),
            "stamp_rate": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg "
                    "focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "نسبة الدمغة",
                }
            ),
            "exchange_rate": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg "
                    "focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "سعر الصرف",
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "class": "w-full px-4 mt-2 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600 transition",
                    "placeholder": "يجب ادخال المصادر هنا",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make company NOT required
        self.fields["company"].required = False
        self.fields["stamp_rate"].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        company = cleaned_data.get("company")
        new_name = cleaned_data.get("new_company_name")

        # ❌ If both fields filled → user selected a company AND typed a new one
        if company and new_name:
            raise forms.ValidationError(
                "لا يمكن اختيار شركة وإدخال شركة جديدة في نفس الوقت. اختر واحدة فقط."
            )

        # ❌ If both empty → already in your code
        if not company and not new_name:
            raise forms.ValidationError(
                "يجب اختيار شركة أو إدخال شركة جديدة."
            )

        if not cleaned_data.get("note"):
            raise forms.ValidationError(
                "يجب ادخال المصادر في حقل الملاحظات."
            )

        return cleaned_data
