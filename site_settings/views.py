from django.shortcuts import render

# Create your views here.


def custom_404_view(request, exception=None):
    return render(request, "404.html", {}, status=404)
