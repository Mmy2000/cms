class ContentSortService:
    SORT_MAP = {
        "newest": "-created_at",
        "oldest": "created_at",
        "title": "title",
    }

    @classmethod
    def apply_sort(cls, queryset, sort_key):
        order_by = cls.SORT_MAP.get(sort_key, "title")
        return queryset.order_by(order_by)
