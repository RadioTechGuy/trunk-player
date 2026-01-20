"""
Trunk Player v2 - Create Test Data Command

Creates sample systems, talkgroups, units, and transmissions for testing.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from radio.models import System, TalkGroup, Unit, Transmission, TransmissionUnit


class Command(BaseCommand):
    help = "Create test data for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--systems",
            type=int,
            default=2,
            help="Number of systems to create (default: 2)",
        )
        parser.add_argument(
            "--transmissions",
            type=int,
            default=15,
            help="Number of transmissions per system (default: 15)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Clear existing test data first",
        )

    def handle(self, *args, **options):
        num_systems = options["systems"]
        num_transmissions = options["transmissions"]
        clear = options["clear"]

        if clear:
            self.stdout.write("Clearing existing data...")
            Transmission.objects.all().delete()
            Unit.objects.all().delete()
            TalkGroup.objects.all().delete()
            System.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared all data"))

        # Sample data for realistic-looking test entries
        system_data = [
            {"name": "Metro County", "description": "Metropolitan county public safety"},
            {"name": "State Highway Patrol", "description": "State highway patrol communications"},
            {"name": "City Fire Department", "description": "City fire and EMS dispatch"},
            {"name": "Regional Transit", "description": "Regional transit authority"},
        ]

        talkgroup_data = [
            {"alpha_tag": "PD Disp", "common_name": "Police Dispatch", "base_id": 1000},
            {"alpha_tag": "PD Tac 1", "common_name": "Police Tactical 1", "base_id": 1001},
            {"alpha_tag": "PD Tac 2", "common_name": "Police Tactical 2", "base_id": 1002},
            {"alpha_tag": "FD Disp", "common_name": "Fire Dispatch", "base_id": 2000},
            {"alpha_tag": "FD Tac 1", "common_name": "Fire Tactical 1", "base_id": 2001},
            {"alpha_tag": "FD Grnd", "common_name": "Fire Ground", "base_id": 2002},
            {"alpha_tag": "EMS Disp", "common_name": "EMS Dispatch", "base_id": 3000},
            {"alpha_tag": "EMS Tac", "common_name": "EMS Tactical", "base_id": 3001},
            {"alpha_tag": "DPW Main", "common_name": "Public Works", "base_id": 4000},
            {"alpha_tag": "Admin", "common_name": "Administration", "base_id": 5000},
        ]

        unit_data = [
            {"desc": "Car 1", "type": "M", "number": "C-1"},
            {"desc": "Car 2", "type": "M", "number": "C-2"},
            {"desc": "Car 3", "type": "M", "number": "C-3"},
            {"desc": "Engine 51", "type": "M", "number": "E-51"},
            {"desc": "Engine 52", "type": "M", "number": "E-52"},
            {"desc": "Ladder 1", "type": "M", "number": "L-1"},
            {"desc": "Medic 1", "type": "M", "number": "M-1"},
            {"desc": "Medic 2", "type": "M", "number": "M-2"},
            {"desc": "Dispatch", "type": "D", "number": "DISP"},
            {"desc": "Chief 1", "type": "M", "number": "CHF-1"},
        ]

        frequencies = [
            851250000, 852500000, 853750000, 854125000,
            855500000, 856250000, 857000000, 858500000,
        ]

        created_systems = 0
        created_talkgroups = 0
        created_units = 0
        created_transmissions = 0

        for i in range(min(num_systems, len(system_data))):
            sys_info = system_data[i]

            system, created = System.objects.get_or_create(
                name=sys_info["name"],
                defaults={"description": sys_info["description"]}
            )
            if created:
                created_systems += 1
                self.stdout.write(f"Created system: {system.name}")
            else:
                self.stdout.write(f"Using existing system: {system.name}")

            # Create talkgroups for this system
            talkgroups = []
            for tg_info in talkgroup_data:
                tg, created = TalkGroup.objects.get_or_create(
                    system=system,
                    dec_id=tg_info["base_id"] + (i * 10000),  # Offset by system
                    defaults={
                        "alpha_tag": tg_info["alpha_tag"],
                        "common_name": tg_info["common_name"],
                        "description": f"{tg_info['common_name']} for {system.name}",
                    }
                )
                talkgroups.append(tg)
                if created:
                    created_talkgroups += 1

            self.stdout.write(f"  Created {len(talkgroups)} talkgroups")

            # Create units for this system
            units = []
            for j, unit_info in enumerate(unit_data):
                unit, created = Unit.objects.get_or_create(
                    system=system,
                    dec_id=100 + j + (i * 1000),  # Offset by system
                    defaults={
                        "description": unit_info["desc"],
                        "unit_type": unit_info["type"],
                        "unit_number": unit_info["number"],
                    }
                )
                units.append(unit)
                if created:
                    created_units += 1

            self.stdout.write(f"  Created {len(units)} units")

            # Create transmissions
            now = timezone.now()
            for t in range(num_transmissions):
                # Random time in the last 24 hours
                start_time = now - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59)
                )

                # Random duration 3-60 seconds
                duration = random.randint(3, 60)
                end_time = start_time + timedelta(seconds=duration)

                # Pick a random talkgroup
                tg = random.choice(talkgroups)

                transmission = Transmission.objects.create(
                    system=system,
                    talkgroup_info=tg,
                    talkgroup=tg.dec_id,
                    start_datetime=start_time,
                    end_datetime=end_time,
                    play_length=duration,
                    audio_file=f"test_{system.slug}_{t+1:03d}.mp3",
                    audio_file_url_path=f"/audio/{system.slug}/test_{t+1:03d}.mp3",
                    freq=random.choice(frequencies),
                    emergency=random.random() < 0.05,  # 5% emergency
                    has_audio=False,  # No actual audio files
                )
                created_transmissions += 1

                # Add 1-3 random units to each transmission
                num_units = random.randint(1, 3)
                selected_units = random.sample(units, min(num_units, len(units)))
                for order, unit in enumerate(selected_units):
                    TransmissionUnit.objects.create(
                        transmission=transmission,
                        unit=unit,
                        order=order
                    )

            self.stdout.write(f"  Created {num_transmissions} transmissions")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created:\n"
            f"  - {created_systems} systems\n"
            f"  - {created_talkgroups} talkgroups\n"
            f"  - {created_units} units\n"
            f"  - {created_transmissions} transmissions"
        ))
