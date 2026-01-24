import csv
from django.core.management.base import BaseCommand
from stamps.models import StampCalculation


class Command(BaseCommand):
    help = "Export Stamp Calculations to CSV for ERPNext"

    def handle(self, *args, **options):
        file_name = "stamp_calculations.csv"

        with open(file_name, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    "User",
                    "Company",
                    "Value Of Work (A)",
                    "Invoice Copies (B)",
                    "Invoice Date",
                    "Stamp Rate (C)",
                    "Exchange Rate",
                    "Total Stamp Duty (D1)",
                    "Total Past Years",
                    "Total Stamp",
                    "Note",
                    "Created At",
                ]
            )

            for obj in StampCalculation.objects.select_related("user", "company"):
                writer.writerow(
                    [
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
                        obj.created_at,
                    ]
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {StampCalculation.objects.count()} records to {file_name}"
            )
        )
