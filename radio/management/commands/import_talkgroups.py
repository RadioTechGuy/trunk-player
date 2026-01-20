"""
Trunk Player v2 - Import Talkgroups Command

Imports talkgroup data from CSV files (Trunk Recorder or Radio Reference format).
"""

import csv

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from radio.models import System, TalkGroup


class Command(BaseCommand):
    help = "Import talkgroup data from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("file", help="Path to CSV file")
        parser.add_argument(
            "--system",
            type=str,
            required=True,
            help="System name or ID",
        )
        parser.add_argument(
            "--rr",
            dest="rr_format",
            action="store_true",
            default=False,
            help="Use Radio Reference CSV format",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            default=False,
            help="Update existing talkgroups",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            default=True,
            help="Truncate data that exceeds field limits",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        system_ref = options["system"]
        rr_format = options["rr_format"]
        update = options["update"]
        truncate = options["truncate"]

        # Get or create system
        try:
            if system_ref.isdigit():
                system = System.objects.get(pk=int(system_ref))
            else:
                system, created = System.objects.get_or_create(name=system_ref)
                if created:
                    self.stdout.write(f"Created new system: {system.name}")
        except System.DoesNotExist:
            self.stdout.write("Available systems:")
            for s in System.objects.all():
                self.stdout.write(f"  #{s.pk} - {s.name}")
            raise CommandError(f"System '{system_ref}' not found")

        self.stdout.write(f"Importing talkgroups for: {system.name}")

        # Get field max lengths
        alpha_tag_max = TalkGroup._meta.get_field("alpha_tag").max_length
        common_name_max = TalkGroup._meta.get_field("common_name").max_length
        description_max = 500  # TextField has no max_length

        imported = 0
        updated = 0
        errors = 0

        try:
            with open(file_path, "r", encoding="utf-8-sig") as csvfile:
                reader = csv.reader(csvfile)

                for line_num, row in enumerate(reader, start=1):
                    if not row or len(row) < 4:
                        continue

                    try:
                        if rr_format:
                            # Radio Reference format:
                            # dec_id, hex_id, alpha_tag, mode, description, tag, category
                            dec_id = int(row[0])
                            alpha_tag = row[2] if len(row) > 2 else ""
                            description = row[4] if len(row) > 4 else ""
                        else:
                            # Trunk Recorder format:
                            # dec_id, hex_id, mode, alpha_tag, description, tag, category, priority
                            dec_id = int(row[0])
                            alpha_tag = row[3] if len(row) > 3 else ""
                            description = row[4] if len(row) > 4 else ""

                        # Truncate if needed
                        if truncate:
                            if len(alpha_tag) > alpha_tag_max:
                                alpha_tag = alpha_tag[:alpha_tag_max]
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  Line {line_num}: Truncated alpha_tag"
                                    )
                                )

                        # Create or update
                        defaults = {
                            "alpha_tag": alpha_tag,
                            "description": description,
                        }

                        tg, created = TalkGroup.objects.get_or_create(
                            dec_id=dec_id,
                            system=system,
                            defaults=defaults,
                        )

                        if created:
                            imported += 1
                        elif update:
                            tg.alpha_tag = alpha_tag
                            tg.description = description
                            tg.save()
                            updated += 1

                    except (ValueError, IndexError) as e:
                        errors += 1
                        if errors <= 10:
                            self.stdout.write(
                                self.style.ERROR(f"  Line {line_num}: {e}")
                            )
                    except IntegrityError:
                        errors += 1

        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Imported: {imported}, Updated: {updated}, Errors: {errors}"
            )
        )
