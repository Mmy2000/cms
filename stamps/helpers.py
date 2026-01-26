from stamps.services.erp_service import ERPNextClient
import logging

from stamps.templatetags.number_filters import millions

logger = logging.getLogger(__name__)


def map_stamp_calculation(obj):
    return {
        "django_id": obj.id,
        "user": obj.user.profile.full_name() if obj.user else "Django System",
        "company": obj.company.name,
        "value_of_work_a": millions(obj.value_of_work),
        "invoice_copies_b": obj.invoice_copies,
        "invoice_date": obj.invoice_date.isoformat() if obj.invoice_date else None,
        "stamp_rate_c": float(obj.stamp_rate),
        "exchange_rate": float(obj.exchange_rate),
        "total_stamp_duty_d1": millions(obj.d1),
        "total_past_years": millions(obj.total_past_years),
        "total_stamp": millions(obj.total_stamp_for_company),
        "note": obj.note or "",
        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def map_expected_stamp(obj):
    return {
        "django_id": obj.id,
        "user": obj.user.profile.full_name() if obj.user else "Django System",
        "sector": obj.sector.name,
        "value_of_work_a": millions(obj.value_of_work),
        "invoice_copies_b": obj.invoice_copies,
        "invoice_date": obj.invoice_date.isoformat() if obj.invoice_date else None,
        "stamp_rate_c": float(obj.stamp_rate),
        "exchange_rate": float(obj.exchange_rate),
        "total_stamp_duty_d1": millions(obj.d1),
        "total_past_years": millions(obj.total_past_years),
        "total_stamp": millions(obj.total_stamp_for_company),
        "note": obj.note or "",
        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def sync_to_erpnext(doctype, instance, data):
    """
    Sync Django model instance to ERPNext.
    First tries to update, if not found, creates new record.
    """
    client = ERPNextClient()
    django_id = instance.id

    data = data.copy()  # prevent mutation side effects

    try:
        # Try to update first
        res = client.update_by_django_id(doctype, django_id, data)

        # Check if update failed due to record not existing
        if isinstance(res, dict):
            message = res.get("message", {})

            # Handle error in update response
            if isinstance(message, dict) and message.get("error"):
                error_msg = message.get("error", "")
                if "not found" in error_msg.lower() or "no " in error_msg.lower():
                    logger.info(
                        f"{doctype} with django_id={django_id} not found in ERPNext, creating new record"
                    )
                    data["django_id"] = django_id
                    create_res = client.create(doctype, data)
                    logger.info(
                        f"Created {doctype} in ERPNext: {create_res.get('data', {}).get('name')}"
                    )
                    return create_res
                else:
                    raise Exception(f"ERPNext update error: {error_msg}")

            # Update was successful
            elif isinstance(message, dict) and message.get("success"):
                logger.info(f"Updated {doctype} in ERPNext: {message.get('name')}")
                return res

            # Handle string message (some APIs return this)
            elif isinstance(message, str):
                logger.info(f"ERPNext response: {message}")
                return res

        return res

    except Exception as e:
        logger.error(
            f"Failed to sync {doctype} (django_id={django_id}) to ERPNext: {str(e)}"
        )
        raise
