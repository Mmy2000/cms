# cms/views.py
from django.shortcuts import render, get_object_or_404
from .models import Content


def main_topics(request):
    sort = request.GET.get("sort", "title")

    if sort == "newest":
        topics = Content.objects.filter(parent__isnull=True).order_by("-created_at")
    elif sort == "oldest":
        topics = Content.objects.filter(parent__isnull=True).order_by("created_at")
    else:
        topics = Content.objects.filter(parent__isnull=True).order_by("title")

    return render(request, "cms/main_topics.html", {"topics": topics})


def content_detail(request, id):
    """Show a single content and its subcontents"""
    content = get_object_or_404(Content, id=id)
    sort = request.GET.get("sort", "title")

    if sort == "newest":
        subcontents = content.subcontents.all().order_by("-created_at")
    elif sort == "oldest":
        subcontents = content.subcontents.all().order_by("created_at")
    else:
        subcontents = content.subcontents.all().order_by("title")
    return render(
        request,
        "cms/content_detail.html",
        {"content": content, "subcontents": subcontents},
    )
