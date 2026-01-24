import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from stamps.models import (
    Company,
    Sector,
    StampCalculation,
    ExpectedStamp,
)
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Export all data to multiple CSV files for ERPNext"

    def handle(self, *args, **options):
        export_dir = os.path.join(settings.BASE_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)

        self.export_companies(export_dir)
        self.export_sectors(export_dir)
        self.export_stamp_calculations(export_dir)
        self.export_expected_stamps(export_dir)

        self.stdout.write(self.style.SUCCESS("✅ All CSV files exported successfully"))

    # -----------------------
    def export_companies(self, export_dir):
        path = os.path.join(export_dir, f"companies_{now().date()}.csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["company_name"])

            for obj in Company.objects.all():
                writer.writerow([obj.name])

        self.stdout.write("• companies.csv exported")

    # -----------------------
    def export_sectors(self, export_dir):
        path = os.path.join(export_dir, f"sectors_{now().date()}.csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["sector_name"])

            for obj in Sector.objects.all():
                writer.writerow([obj.name])

        self.stdout.write("• sectors.csv exported")

    # -----------------------
    def export_stamp_calculations(self, export_dir):
        path = os.path.join(export_dir, f"stamp_calculations_{now().date()}.csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "django_id",
                    "user",
                    "company",
                    "value_of_work_a",
                    "invoice_copies_b",
                    "invoice_date",
                    "stamp_rate_c",
                    "exchange_rate",
                    "total_stamp_duty_d1",
                    "total_past_years",
                    "total_stamp",
                    "note",
                    "created_at",
                ]
            )

            for obj in StampCalculation.objects.select_related("user", "company"):
                writer.writerow(
                    [
                        obj.id,
                        obj.user.profile.full_name(),
                        obj.company.name,
                        obj.value_of_work,
                        obj.invoice_copies,
                        obj.invoice_date,
                        obj.stamp_rate,
                        obj.exchange_rate,
                        obj.d1,
                        obj.total_past_years,
                        obj.total_stamp_for_company,
                        obj.note,
                        obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )

        self.stdout.write("• stamp_calculations.csv exported")

    # -----------------------
    def export_expected_stamps(self, export_dir):
        path = os.path.join(export_dir, f"expected_stamps_{now().date()}.csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "django_id",
                    "user",
                    "sector",
                    "value_of_work_a",
                    "invoice_copies_b",
                    "invoice_date",
                    "stamp_rate_c",
                    "exchange_rate",
                    "total_stamp_duty_d1",
                    "total_past_years",
                    "total_stamp",
                    "note",
                    "created_at",
                ]
            )

            for obj in ExpectedStamp.objects.select_related("user", "sector"):
                writer.writerow(
                    [
                        obj.id,
                        obj.user.profile.full_name(),
                        obj.sector.name,
                        obj.value_of_work,
                        obj.invoice_copies,
                        obj.invoice_date,
                        obj.stamp_rate,
                        obj.exchange_rate,
                        obj.d1,
                        obj.total_past_years,
                        obj.total_stamp_for_company,
                        obj.note,
                        obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )

        self.stdout.write("• expected_stamps.csv exported")
