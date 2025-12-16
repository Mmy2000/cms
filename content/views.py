from django.shortcuts import render, get_object_or_404
from content.selectors.content_selector import ContentSelector
from content.services.content_service import ContentSortService


def main_topics(request):
    sort = request.GET.get("sort", "title")

    topics_qs = ContentSelector.main_topics()
    topics = ContentSortService.apply_sort(topics_qs, sort)

    return render(request, "cms/main_topics.html", {"topics": topics})


def content_detail(request, id):
    content = get_object_or_404(ContentSelector.by_id(id))
    sort = request.GET.get("sort", "title")

    subcontents_qs = ContentSelector.subcontents(content)
    subcontents = ContentSortService.apply_sort(subcontents_qs, sort)

    return render(
        request,
        "cms/content_detail.html",
        {
            "content": content,
            "subcontents": subcontents,
        },
    )
