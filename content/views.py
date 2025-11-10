# cms/views.py
from django.shortcuts import render, get_object_or_404
from .models import Content


def main_topics(request):
    """Show all top-level contents"""
    topics = Content.objects.filter(parent__isnull=True)
    return render(request, "cms/main_topics.html", {"topics": topics})


def content_detail(request, slug):
    """Show a single content and its subcontents"""
    content = get_object_or_404(Content, slug=slug)
    subcontents = content.subcontents.all()
    return render(
        request,
        "cms/content_detail.html",
        {"content": content, "subcontents": subcontents},
    )
