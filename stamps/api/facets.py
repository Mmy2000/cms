# stamps/api/facets.py
"""
Reusable facet helpers.

Each function receives an *unfiltered* base queryset (so counts always
reflect the full dataset, not only the currently filtered slice) and
returns a dict ready to be placed under the "filters" key in the response.
"""

from django.db.models import Count, Min, Max


def build_stamp_filters(base_qs, active: dict) -> dict:
    """
    Build the full 'filters' block for StampCalculation list responses.

    Args:
        base_qs:  Unfiltered StampCalculation queryset (used for counts/range).
        active:   Dict of active filter values from the current request,
                  e.g. {"company": "3", "date_from": "2024-01-01", "date_to": None}
    """
    return {
        "active": _clean_active(active),
        "date_range": _date_range(base_qs, "invoice_date"),
        "options": {
            "companies": _company_facets(base_qs),
            "years": _year_facets(base_qs, "invoice_date"),
        },
    }


def build_expected_stamp_filters(base_qs, active: dict) -> dict:
    """
    Build the full 'filters' block for ExpectedStamp list responses.

    Args:
        base_qs:  Unfiltered ExpectedStamp queryset.
        active:   Dict of active filter values from the current request.
    """
    return {
        "active": _clean_active(active),
        "date_range": _date_range(base_qs, "invoice_date"),
        "options": {
            "sectors": _sector_facets(base_qs),
            "years": _year_facets(base_qs, "invoice_date"),
        },
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _clean_active(active: dict) -> dict:
    """Remove None / empty string values so the client only sees what's set."""
    return {k: v for k, v in active.items() if v not in (None, "", "none", "None")}


def _date_range(qs, field: str) -> dict:
    """Return the min and max date present in the queryset for `field`."""
    agg = qs.aggregate(
        min_date=Min(field),
        max_date=Max(field),
    )
    return {
        "min": agg["min_date"].isoformat() if agg["min_date"] else None,
        "max": agg["max_date"].isoformat() if agg["max_date"] else None,
    }


def _company_facets(qs) -> list:
    """
    Return all companies that appear in `qs`, each with a stamp count.
    Ordered by count descending so the most common appear first.
    """
    rows = (
        qs.values("company_id", "company__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [
        {"id": row["company_id"], "name": row["company__name"], "count": row["count"]}
        for row in rows
    ]


def _sector_facets(qs) -> list:
    """
    Return all sectors that appear in `qs`, each with a record count.
    Ordered by count descending.
    """
    rows = (
        qs.values("sector_id", "sector__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [
        {"id": row["sector_id"], "name": row["sector__name"], "count": row["count"]}
        for row in rows
    ]


def _year_facets(qs, date_field: str) -> list:
    """
    Return a count per year derived from `date_field`, ordered newest first.
    Records where the date is NULL are excluded.
    """
    rows = (
        qs.exclude(**{f"{date_field}__isnull": True})
        .values(f"{date_field}__year")
        .annotate(count=Count("id"))
        .order_by(f"-{date_field}__year")
    )
    return [{"year": row[f"{date_field}__year"], "count": row["count"]} for row in rows]
