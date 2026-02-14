from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        # data may be {"results": [...], "summary": {...}, "filters": {...}} from the view
        # or just a list if called from a standard ListAPIView
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            summary = data.get("summary", {})
            facets = data.get("filters", {})
        else:
            results = data
            summary = {}
            facets = {}

        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "summary": summary,
                "filters": facets,
                "results": results,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "summary": {"type": "object"},
                "results": schema,
            },
        }
