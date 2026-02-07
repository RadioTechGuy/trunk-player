"""
Management command to archive old transmissions.

Moves transmissions older than specified days to TransmissionArchive
table to keep the main Transmission table performant.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from radio.models import Transmission, TransmissionArchive


class Command(BaseCommand):
    help = "Archive transmissions older than specified days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Archive transmissions older than this many days (default: 90)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of transmissions to process per batch (default: 1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without making changes",
        )
        parser.add_argument(
            "--delete-after",
            action="store_true",
            help="Delete original transmissions after archiving",
        )

    def handle(self, *args, **options):
        days = options["days"]
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]
        delete_after = options["delete_after"]

        cutoff_date = timezone.now() - timedelta(days=days)

        # Count transmissions to archive
        total_count = Transmission.objects.filter(
            start_datetime__lt=cutoff_date
        ).count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"No transmissions older than {days} days to archive")
            )
            return

        self.stdout.write(
            f"Found {total_count} transmissions older than {days} days"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes made"))
            return

        archived_count = 0
        deleted_count = 0

        while True:
            # Get batch of transmissions to archive
            transmissions = list(
                Transmission.objects.filter(start_datetime__lt=cutoff_date)
                .select_related("system", "talkgroup_info")
                .order_by("start_datetime")[:batch_size]
            )

            if not transmissions:
                break

            # Create archive records
            archives = []
            transmission_ids = []

            for t in transmissions:
                archives.append(
                    TransmissionArchive(
                        original_id=t.id,
                        slug=t.slug,
                        start_datetime=t.start_datetime,
                        end_datetime=t.end_datetime,
                        play_length=t.play_length,
                        audio_file=t.audio_file,
                        system_id=t.system_id,
                        system_name=t.system_name or t.system.name,
                        talkgroup_id=t.talkgroup_info_id,
                        talkgroup_dec_id=t.talkgroup_dec_id,
                        talkgroup_name=t.talkgroup_name or t.talkgroup_info.display_name,
                        units_json=t.units_json,
                        freq=t.freq,
                        emergency=t.emergency,
                        created_at=t.created_at,
                    )
                )
                transmission_ids.append(t.id)

            with transaction.atomic():
                # Bulk create archives
                TransmissionArchive.objects.bulk_create(archives)
                archived_count += len(archives)

                # Delete originals if requested
                if delete_after:
                    Transmission.objects.filter(id__in=transmission_ids).delete()
                    deleted_count += len(transmission_ids)

            self.stdout.write(
                f"  Archived {archived_count}/{total_count} transmissions..."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Archived {archived_count} transmissions"
                + (f", deleted {deleted_count} originals" if delete_after else "")
            )
        )
