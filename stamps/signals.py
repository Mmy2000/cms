from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from stamps.models import ExpectedStamp, StampCalculation


@receiver(post_delete, sender=StampCalculation)
def update_stamp_calculations_after_delete(sender, instance, **kwargs):
    """
    After deleting a StampCalculation, recalculate totals for all remaining records of the same company
    """
    # Get all remaining records for the same company, ordered by creation date
    remaining_records = StampCalculation.objects.filter(
        company=instance.company
    ).order_by("created_at")

    # Recalculate each record's totals
    for record in remaining_records:
        # Calculate past total (all records before this one)
        past_total = (
            StampCalculation.objects.filter(
                company=record.company, created_at__lt=record.created_at
            ).aggregate(models.Sum("d1"))["d1__sum"]
            or 0
        )

        record.total_past_years = past_total
        record.total_stamp_for_company = record.d1 + past_total

        # Use update_fields to avoid triggering save logic recursively
        record.save(update_fields=["total_past_years", "total_stamp_for_company"])


@receiver(post_delete, sender=ExpectedStamp)
def update_expected_stamps_after_delete(sender, instance, **kwargs):
    """
    After deleting an ExpectedStamp, recalculate totals for all remaining records of the same sector
    """
    # Get all remaining records for the same sector, ordered by creation date
    remaining_records = ExpectedStamp.objects.filter(sector=instance.sector).order_by(
        "created_at"
    )

    # Recalculate each record's totals
    for record in remaining_records:
        # Calculate past total (all records before this one)
        past_total = (
            ExpectedStamp.objects.filter(
                sector=record.sector, created_at__lt=record.created_at
            ).aggregate(models.Sum("d1"))["d1__sum"]
            or 0
        )

        record.total_past_years = past_total
        record.total_stamp_for_company = record.d1 + past_total

        # Use update_fields to avoid triggering save logic recursively
        record.save(update_fields=["total_past_years", "total_stamp_for_company"])
