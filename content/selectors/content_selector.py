from ..models import Content


class ContentSelector:
    @staticmethod
    def main_topics():
        return Content.objects.filter(parent__isnull=True)

    @staticmethod
    def by_id(content_id):
        return (
            Content.objects.select_related("parent")
            .prefetch_related("subcontents", "images", "files")
            .filter(id=content_id)
        )

    @staticmethod
    def subcontents(content):
        return content.subcontents.all()
