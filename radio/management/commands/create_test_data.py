"""
Create fake test data: a demo agency system with talkgroups, units, and transmissions.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from radio.models import System, TalkGroup, Unit, Transmission, TransmissionUnit


# Realistic public-safety talkgroup definitions
TALKGROUPS = [
    {"dec_id": 1001, "alpha_tag": "PD Disp", "common_name": "Police Dispatch"},
    {"dec_id": 1002, "alpha_tag": "PD Tac 1", "common_name": "Police Tactical 1"},
    {"dec_id": 1003, "alpha_tag": "PD Tac 2", "common_name": "Police Tactical 2"},
    {"dec_id": 1004, "alpha_tag": "PD Det", "common_name": "Police Detectives"},
    {"dec_id": 1005, "alpha_tag": "PD Traffic", "common_name": "Police Traffic"},
    {"dec_id": 2001, "alpha_tag": "FD Disp", "common_name": "Fire Dispatch"},
    {"dec_id": 2002, "alpha_tag": "FD Tac 1", "common_name": "Fire Tactical 1"},
    {"dec_id": 2003, "alpha_tag": "FD Grnd", "common_name": "Fireground"},
    {"dec_id": 3001, "alpha_tag": "EMS Disp", "common_name": "EMS Dispatch"},
    {"dec_id": 3002, "alpha_tag": "EMS Tac", "common_name": "EMS Tactical"},
    {"dec_id": 4001, "alpha_tag": "DPW Ops", "common_name": "Public Works Operations"},
    {"dec_id": 5001, "alpha_tag": "Admin", "common_name": "Administration"},
]

UNITS = [
    {"dec_id": 101, "desc": "Car 1", "type": "M", "number": "C-1"},
    {"dec_id": 102, "desc": "Car 2", "type": "M", "number": "C-2"},
    {"dec_id": 103, "desc": "Car 3", "type": "M", "number": "C-3"},
    {"dec_id": 104, "desc": "Car 4", "type": "M", "number": "C-4"},
    {"dec_id": 105, "desc": "Sgt 10", "type": "M", "number": "S-10"},
    {"dec_id": 201, "desc": "Engine 51", "type": "M", "number": "E-51"},
    {"dec_id": 202, "desc": "Engine 52", "type": "M", "number": "E-52"},
    {"dec_id": 203, "desc": "Ladder 1", "type": "M", "number": "L-1"},
    {"dec_id": 204, "desc": "Rescue 1", "type": "M", "number": "R-1"},
    {"dec_id": 301, "desc": "Medic 1", "type": "M", "number": "M-1"},
    {"dec_id": 302, "desc": "Medic 2", "type": "M", "number": "M-2"},
    {"dec_id": 401, "desc": "Dispatch", "type": "D", "number": "DISP"},
    {"dec_id": 402, "desc": "Chief 1", "type": "M", "number": "CHF-1"},
    {"dec_id": 403, "desc": "Battalion 1", "type": "M", "number": "BC-1"},
]

FREQUENCIES = [
    851250000, 852500000, 853750000, 854125000,
    855500000, 856250000, 857000000, 858500000,
    460125000, 460275000, 460525000, 462575000,
]


class Command(BaseCommand):
    help = "Create a fake agency with talkgroups, units, and ~50 transmissions for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            default="Demo County",
            help="System/agency name (default: Demo County)",
        )
        parser.add_argument(
            "--transmissions",
            type=int,
            default=50,
            help="Number of transmissions to create (default: 50)",
        )
        parser.add_argument(
            "--hours",
            type=int,
            default=4,
            help="Spread transmissions over this many hours back from now (default: 4)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Delete existing data for this system first",
        )

    def handle(self, *args, **options):
        system_name = options["name"]
        num_trans = options["transmissions"]
        hours_back = options["hours"]
        clear = options["clear"]

        if clear:
            try:
                existing = System.objects.get(name=system_name)
                Transmission.objects.filter(system=existing).delete()
                TransmissionUnit.objects.filter(
                    transmission__system=existing
                ).delete()
                Unit.objects.filter(system=existing).delete()
                TalkGroup.objects.filter(system=existing).delete()
                existing.delete()
                self.stdout.write(self.style.WARNING(
                    f"Cleared existing data for '{system_name}'"
                ))
            except System.DoesNotExist:
                pass

        # Create system
        system, created = System.objects.get_or_create(
            name=system_name,
            defaults={"description": f"{system_name} Public Safety"}
        )
        status = "Created" if created else "Using existing"
        self.stdout.write(f"{status} system: {system.name}")

        # Create talkgroups
        talkgroups = []
        for tg_data in TALKGROUPS:
            tg, _ = TalkGroup.objects.get_or_create(
                system=system,
                dec_id=tg_data["dec_id"],
                defaults={
                    "alpha_tag": tg_data["alpha_tag"],
                    "common_name": tg_data["common_name"],
                    "description": f"{tg_data['common_name']} for {system_name}",
                },
            )
            talkgroups.append(tg)
        self.stdout.write(f"  {len(talkgroups)} talkgroups ready")

        # Create units
        units = []
        for u_data in UNITS:
            unit, _ = Unit.objects.get_or_create(
                system=system,
                dec_id=u_data["dec_id"],
                defaults={
                    "description": u_data["desc"],
                    "unit_type": u_data["type"],
                    "unit_number": u_data["number"],
                },
            )
            units.append(unit)
        self.stdout.write(f"  {len(units)} units ready")

        # Weight dispatch talkgroups higher for realism
        dispatch_tgs = [tg for tg in talkgroups if "Disp" in tg.alpha_tag]
        tac_tgs = [tg for tg in talkgroups if tg not in dispatch_tgs]
        weights = [3 if tg in dispatch_tgs else 1 for tg in talkgroups]

        # Create transmissions spread over the time window
        now = timezone.now()
        created_count = 0

        for i in range(num_trans):
            # Spread evenly then jitter
            base_offset = (hours_back * 3600) * (i / max(num_trans - 1, 1))
            jitter = random.randint(-120, 120)
            offset_secs = max(0, base_offset + jitter)
            start_time = now - timedelta(seconds=offset_secs)

            duration = random.randint(3, 45)
            end_time = start_time + timedelta(seconds=duration)

            tg = random.choices(talkgroups, weights=weights, k=1)[0]

            # Pick relevant units based on talkgroup type
            if "PD" in tg.alpha_tag:
                pool = [u for u in units if u.dec_id < 200 or u.dec_id >= 400]
            elif "FD" in tg.alpha_tag:
                pool = [u for u in units if 200 <= u.dec_id < 300 or u.dec_id >= 400]
            elif "EMS" in tg.alpha_tag:
                pool = [u for u in units if 300 <= u.dec_id < 400 or u.dec_id >= 400]
            else:
                pool = units

            num_units = random.randint(1, min(3, len(pool)))
            selected_units = random.sample(pool, num_units)

            units_json = [
                {"id": u.dec_id, "name": u.display_name}
                for u in selected_units
            ]

            is_emergency = random.random() < 0.04  # ~4% chance

            transmission = Transmission(
                system=system,
                talkgroup_info=tg,
                talkgroup_dec_id=tg.dec_id,
                talkgroup_name=tg.display_name,
                system_name=system.name,
                start_datetime=start_time,
                end_datetime=end_time,
                play_length=duration,
                audio_file=f"demo/{system.slug}/call_{i + 1:04d}.mp3",
                freq=random.choice(FREQUENCIES),
                emergency=is_emergency,
                units_json=units_json,
            )
            transmission.save()
            created_count += 1

            # Also create TransmissionUnit records
            for order, unit in enumerate(selected_units):
                TransmissionUnit.objects.create(
                    transmission=transmission,
                    unit=unit,
                    order=order,
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {created_count} transmissions for '{system_name}'\n"
            f"  System: {system.name} (slug: {system.slug})\n"
            f"  Talkgroups: {len(talkgroups)}\n"
            f"  Units: {len(units)}\n"
            f"  Transmissions: {created_count}\n"
            f"  Time span: last {hours_back} hours"
        ))
