# Populate denormalized fields on Transmission

from django.db import migrations


def populate_denormalized_fields(apps, schema_editor):
    """
    Populate talkgroup_name, system_name, and units_json
    for existing transmissions.
    """
    Transmission = apps.get_model('radio', 'Transmission')
    TransmissionUnit = apps.get_model('radio', 'TransmissionUnit')

    # Update in batches for large datasets
    batch_size = 1000
    total = Transmission.objects.count()

    if total == 0:
        return

    print(f"\nPopulating denormalized fields for {total} transmissions...")

    processed = 0
    while processed < total:
        transmissions = list(
            Transmission.objects.select_related('system', 'talkgroup_info')
            .order_by('id')[processed:processed + batch_size]
        )

        for t in transmissions:
            updates = {}

            # Denormalize talkgroup name
            if not t.talkgroup_name and t.talkgroup_info:
                tg = t.talkgroup_info
                updates['talkgroup_name'] = tg.common_name or tg.alpha_tag or f"TG {tg.dec_id}"

            # Denormalize system name
            if not t.system_name and t.system:
                updates['system_name'] = t.system.name

            # Denormalize units
            if not t.units_json:
                units = list(
                    TransmissionUnit.objects.filter(transmission=t)
                    .select_related('unit')
                    .order_by('order')
                )
                if units:
                    updates['units_json'] = [
                        {
                            'id': tu.unit.dec_id,
                            'name': tu.unit.description or str(tu.unit.dec_id)
                        }
                        for tu in units
                    ]

            if updates:
                Transmission.objects.filter(pk=t.pk).update(**updates)

        processed += len(transmissions)
        if processed % 10000 == 0:
            print(f"  Processed {processed}/{total}...")

    print(f"  Done. Processed {total} transmissions.")


def reverse_migration(apps, schema_editor):
    """No need to reverse - denormalized data can stay."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0004_transmission_scale_optimization'),
    ]

    operations = [
        migrations.RunPython(
            populate_denormalized_fields,
            reverse_migration,
        ),
    ]
