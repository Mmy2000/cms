
from django.shortcuts import render
from .models import About


def about_page(request):
    about = About.objects.prefetch_related("values").first()

    return render(
        request,
        "about.html",
        {
            "about": about,
        },
    )
