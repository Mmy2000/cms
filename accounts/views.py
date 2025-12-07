# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(
                request, "تم إنشاء الحساب بنجاح ✅ سيتم مراجعة بياناتك ثم تفعيل الحساب."
            )
            return redirect("login")
        else:
            messages.error(request, "من فضلك صحح الأخطاء بالأسفل")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    pass