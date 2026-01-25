from stamps.services.erp_service import ERPNextClient


def map_stamp_calculation(obj):
    return {
        "django_id": obj.id,
        "user": obj.user.profile.full_name() if obj.user else "Django System",
        "company": obj.company.name,
        "value_of_work_a": float(obj.value_of_work),
        "invoice_copies_b": obj.invoice_copies,
        "invoice_date": obj.invoice_date.isoformat() if obj.invoice_date else None,
        "stamp_rate_c": float(obj.stamp_rate),
        "exchange_rate": float(obj.exchange_rate),
        "total_stamp_duty_d1": float(obj.d1),
        "total_past_years": float(obj.total_past_years),
        "total_stamp": float(obj.total_stamp_for_company),
        "note": obj.note or "",
        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }

def map_expected_stamp(obj):
    return {
        "django_id": obj.id,
        "user": obj.user.profile.full_name() if obj.user else "Django System",
        "sector": obj.sector.name,
        "value_of_work_a": float(obj.value_of_work),
        "invoice_copies_b": obj.invoice_copies,
        "invoice_date": obj.invoice_date.isoformat() if obj.invoice_date else None,
        "stamp_rate_c": float(obj.stamp_rate),
        "exchange_rate": float(obj.exchange_rate),
        "total_stamp_duty_d1": float(obj.d1),
        "total_past_years": float(obj.total_past_years),
        "total_stamp": float(obj.total_stamp_for_company),
        "note": obj.note or "",
        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def sync_to_erpnext(doctype, instance, data):
    client = ERPNextClient()
    django_id = instance.id

    data = data.copy()  # prevent mutation side effects

    res = client.update_by_django_id(doctype, django_id, data)

    # ERPNext logical error → create
    if isinstance(res, dict) and res.get("message", {}).get("error"):
        data["django_id"] = django_id
        client.create(doctype, data)
        return