"""
Trunk Player v2 - Prune Database Command

Removes old transmissions from the database to manage storage.
"""

import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, connections, transaction
from django.utils import timezone

from radio.models import Transmission


class Command(BaseCommand):
    help = "Remove old transmissions from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete transmissions older than this many days (default: 30)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--vacuum",
            action="store_true",
            default=False,
            help="Vacuum SQLite database after pruning (SQLite only)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        vacuum = options["vacuum"]

        if days < 1:
            self.stdout.write(
                self.style.ERROR("Days must be at least 1")
            )
            return

        cutoff_date = timezone.now() - timedelta(days=days)

        # Count transmissions to delete
        transmissions = Transmission.objects.filter(
            start_datetime__lt=cutoff_date
        )
        count = transmissions.count()

        if count == 0:
            self.stdout.write("No transmissions to prune.")
            return

        self.stdout.write(
            f"Found {count} transmissions older than {days} days"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry run - no data will be deleted")
            )

            # Show sample of what would be deleted
            sample = transmissions.order_by("start_datetime")[:5]
            self.stdout.write("\nOldest transmissions that would be deleted:")
            for t in sample:
                self.stdout.write(
                    f"  {t.slug} - {t.start_datetime} - {t.talkgroup_info}"
                )
            return

        # Delete transmissions
        self.stdout.write(f"Deleting {count} transmissions...")
        deleted, _ = transmissions.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} transmissions")
        )

        # Vacuum SQLite if requested
        db_engine = connection.vendor
        if vacuum and "sqlite" in db_engine:
            db_name = connection.settings_dict["NAME"]

            self.stdout.write("Vacuuming SQLite database...")
            try:
                before = os.stat(db_name).st_size
                cursor = connections["default"].cursor()
                cursor.execute("VACUUM")
                transaction.commit()
                after = os.stat(db_name).st_size

                reclaimed = before - after
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Reclaimed {reclaimed:,} bytes "
                        f"({before:,} -> {after:,})"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Vacuum failed: {e}")
                )
        elif vacuum:
            self.stdout.write(
                self.style.WARNING(
                    "Vacuum only supported for SQLite databases"
                )
            )
