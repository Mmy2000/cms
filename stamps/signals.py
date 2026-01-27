from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from stamps.helpers import map_expected_stamp, map_stamp_calculation
from stamps.models import ExpectedStamp, StampCalculation
from stamps.tasks import  delete_stamp_from_erpnext_task, recalculate_expected_stamps_task, recalculate_stamp_calculations_task, sync_expected_stamp_to_erpnext_task, sync_stamp_to_erpnext_task
import logging

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=StampCalculation)
def handle_stamp_calculation_delete(sender, instance, **kwargs):
    """
    After deleting a StampCalculation:
    1. Delete from ERPNext
    2. Recalculate totals for all remaining records of the same company
    """
    company_id = instance.company.id

    logger.info(f"Deleting StampCalculation {instance.id} - queuing ERPNext deletion")
    delete_stamp_from_erpnext_task.enqueue(instance.id, "Stamp Calculation")

    logger.info(
        f"Queuing recalculation for company {company_id} after StampCalculation {instance.id} deletion"
    )
    recalculate_stamp_calculations_task.enqueue(company_id)


@receiver(post_delete, sender=ExpectedStamp)
def handle_expected_stamp_delete(sender, instance, **kwargs):
    """
    After deleting an ExpectedStamp:
    1. Delete from ERPNext
    2. Recalculate totals for all remaining records of the same sector
    """
    sector_id = instance.sector.id

    logger.info(f"Deleting ExpectedStamp {instance.id} - queuing ERPNext deletion")
    delete_stamp_from_erpnext_task.enqueue(instance.id, "Expected Stamp")

    logger.info(
        f"Queuing recalculation for sector {sector_id} after ExpectedStamp {instance.id} deletion"
    )
    recalculate_expected_stamps_task.enqueue(sector_id)


# Signal receivers - these run synchronously but queue background tasks
@receiver(post_save, sender=StampCalculation)
def sync_stamp_to_erpnext(sender, instance, **kwargs):
    data = map_stamp_calculation(instance)
    sync_stamp_to_erpnext_task.enqueue(instance.id, data)


@receiver(post_save, sender=ExpectedStamp)
def sync_expected_stamp_to_erpnext(sender, instance, **kwargs):
    data = map_expected_stamp(instance)
    sync_expected_stamp_to_erpnext_task.enqueue(instance.id, data)
