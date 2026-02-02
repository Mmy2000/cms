from django.tasks import task
from stamps.helpers import map_expected_stamp, map_stamp_calculation, sync_to_erpnext
from stamps.services.erp_service import ERPNextClient
from .models import Company, Sector, StampCalculation, ExpectedStamp
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.db import models

logger = logging.getLogger(__name__)


# ============================================================================
# SYNC TASKS
# ============================================================================

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
        send_email.enqueue(
            to_email=settings.DEFAULT_FROM_EMAIL,
            first_name="Admin",
            subject="ERPNext Sync Failure Alert",
            message=f"Failed to sync StampCalculation {instance_id} to ERPNext. Error: {str(e)}",
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
        send_email.enqueue(
            to_email=settings.DEFAULT_FROM_EMAIL,
            first_name="Admin",
            subject="ERPNext Sync Failure Alert",
            message=f"Failed to sync ExpectedStamp {instance_id} to ERPNext. Error: {str(e)}",
        )
        raise


# ============================================================================
# DELETE TASKS
# ============================================================================

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
        send_email.enqueue(
            to_email=settings.DEFAULT_FROM_EMAIL,
            first_name="Admin",
            subject="ERPNext Deletion Failure Alert",
            message=f"Failed to delete {doctype} {django_id} from ERPNext. Error: {str(e)}",
        )
        raise

# ============================================================================
# EMAIL TASKS
# ============================================================================

@task()
def send_email(to_email, first_name, subject, message):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )


# ============================================================================
# RECALCULATION TASKS
# ============================================================================

@task()
def recalculate_stamp_calculations_task(company_id):
    """Optimized version using bulk_update"""
    lock_key = f"recalc_stamp_company_{company_id}"

    if not cache.add(lock_key, "locked", timeout=300):
        logger.info(f"Skipping duplicate recalculation for company {company_id}")
        return None

    try:
        company = Company.objects.get(id=company_id)
        remaining_records = StampCalculation.objects.filter(company=company).order_by(
            "created_at"
        )

        records_to_update = []

        for record in remaining_records:
            past_total = (
                StampCalculation.objects.filter(
                    company=record.company, created_at__lt=record.created_at
                ).aggregate(models.Sum("d1"))["d1__sum"]
                or 0
            )

            if (
                record.total_past_years != past_total
                or record.total_stamp_for_company != (record.d1 + past_total)
            ):
                record.total_past_years = past_total
                record.total_stamp_for_company = record.d1 + past_total
                records_to_update.append(record)
            
            data = map_stamp_calculation(record)
            sync_stamp_to_erpnext_task.enqueue(record.id, data)

        # Bulk update all records at once
        if records_to_update:
            StampCalculation.objects.bulk_update(
                records_to_update, ["total_past_years", "total_stamp_for_company"]
            )

        logger.info(
            f"Bulk updated {len(records_to_update)} StampCalculation records for company {company.name}"
        )
        return {"company_id": company_id, "updated_records": len(records_to_update)}

    except Exception as e:
        logger.error(
            f"Recalculation failed for company {company_id}: {str(e)}", exc_info=True
        )
        raise
    finally:
        cache.delete(lock_key)


@task()
def recalculate_expected_stamps_task(sector_id):
    """Optimized version using bulk_update for ExpectedStamp"""
    lock_key = f"recalc_expected_sector_{sector_id}"

    if not cache.add(lock_key, "locked", timeout=300):
        logger.info(f"Skipping duplicate recalculation for sector {sector_id}")
        return None

    try:
        sector = Sector.objects.get(id=sector_id)
        remaining_records = ExpectedStamp.objects.filter(sector=sector).order_by(
            "created_at"
        )

        records_to_update = []

        for record in remaining_records:
            past_total = (
                ExpectedStamp.objects.filter(
                    sector=record.sector, created_at__lt=record.created_at
                ).aggregate(models.Sum("d1"))["d1__sum"]
                or 0
            )

            if (
                record.total_past_years != past_total
                or record.total_stamp_for_company != (record.d1 + past_total)
            ):
                record.total_past_years = past_total
                record.total_stamp_for_company = record.d1 + past_total
                records_to_update.append(record)
            
            data = map_expected_stamp(record)
            sync_expected_stamp_to_erpnext_task.enqueue(record.id, data)

        # Bulk update all records at once
        if records_to_update:
            ExpectedStamp.objects.bulk_update(
                records_to_update, ["total_past_years", "total_stamp_for_company"]
            )

        logger.info(
            f"Bulk updated {len(records_to_update)} ExpectedStamp records for sector {sector.name}"
        )
        return {"sector_id": sector_id, "updated_records": len(records_to_update)}

    except Sector.DoesNotExist:
        logger.warning(f"Sector {sector_id} no longer exists")
        return None
    except Exception as e:
        logger.error(
            f"Recalculation failed for sector {sector_id}: {str(e)}", exc_info=True
        )
        raise
    finally:
        cache.delete(lock_key)
