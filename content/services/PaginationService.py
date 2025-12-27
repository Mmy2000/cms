from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class PaginationService:
    DEFAULT_PAGE_SIZE = 9

    @classmethod
    def paginate(cls, queryset, request, page_size=None):
        """
        Paginate a queryset based on request parameters.

        Args:
            queryset: The queryset to paginate
            request: The Django request object
            page_size: Number of items per page (defaults to DEFAULT_PAGE_SIZE)

        Returns:
            tuple: (paginated_page, paginator)
        """
        if page_size is None:
            page_size = cls.DEFAULT_PAGE_SIZE

        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, page_size)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return page, paginator

    @classmethod
    def get_context(cls, queryset, request, page_size=None):
        """
        Get pagination context for templates.

        Args:
            queryset: The queryset to paginate
            request: The Django request object
            page_size: Number of items per page

        Returns:
            dict: Context dictionary with 'page' and 'paginator'
        """
        page, paginator = cls.paginate(queryset, request, page_size)
        return {
            "page": page,
            "paginator": paginator,
        }
