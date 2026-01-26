from django.tasks import task
from stamps.helpers import sync_to_erpnext
from stamps.services.erp_service import ERPNextClient
from .models import StampCalculation, ExpectedStamp
import logging

logger = logging.getLogger(__name__)


@task()
def sync_stamp_to_erpnext_task(instance_id, data):
    """Background task to sync stamp calculation to ERPNext"""
    try:
        instance = StampCalculation.objects.get(id=instance_id)
        result = sync_to_erpnext("Stamp Calculation", instance, data)
        logger.info(f"Successfully synced StampCalculation {instance_id} to ERPNext")
        return result
    except StampCalculation.DoesNotExist:
        logger.warning(f"StampCalculation {instance_id} no longer exists")
        return None
    except Exception as e:
        logger.error(
            f"ERPNext sync failed for StampCalculation {instance_id}: {str(e)}",
            exc_info=True,
        )
        raise  # Re-raise to mark task as failed


@task()
def sync_expected_stamp_to_erpnext_task(instance_id, data):
    """Background task to sync expected stamp to ERPNext"""
    try:
        instance = ExpectedStamp.objects.get(id=instance_id)
        result = sync_to_erpnext("Expected Stamp", instance, data)
        logger.info(f"Successfully synced ExpectedStamp {instance_id} to ERPNext")
        return result
    except ExpectedStamp.DoesNotExist:
        logger.warning(f"ExpectedStamp {instance_id} no longer exists")
        return None
    except Exception as e:
        logger.error(
            f"ERPNext sync failed for ExpectedStamp {instance_id}: {str(e)}",
            exc_info=True,
        )
        raise


@task()
def delete_stamp_from_erpnext_task(django_id, doctype):
    """Background task to delete stamp from ERPNext"""
    client = ERPNextClient()
    try:
        result = client.delete_by_django_id(doctype, django_id)
        logger.info(f"Successfully deleted {doctype} {django_id} from ERPNext")
        return result
    except Exception as e:
        logger.error(
            f"ERPNext delete failed for {doctype} {django_id}: {str(e)}", exc_info=True
        )
        raise
