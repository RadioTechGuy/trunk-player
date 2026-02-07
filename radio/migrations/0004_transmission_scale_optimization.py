# Transmission model optimization for millions of records

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0003_add_favorite_talkgroups'),
    ]

    operations = [
        # Rename talkgroup to talkgroup_dec_id for clarity
        migrations.RenameField(
            model_name='transmission',
            old_name='talkgroup',
            new_name='talkgroup_dec_id',
        ),

        # Add denormalized fields for fast reads
        migrations.AddField(
            model_name='transmission',
            name='talkgroup_name',
            field=models.CharField(blank=True, help_text='Talkgroup display name (denormalized)', max_length=100),
        ),
        migrations.AddField(
            model_name='transmission',
            name='system_name',
            field=models.CharField(blank=True, help_text='System name (denormalized)', max_length=100),
        ),

        # Add JSON field for units (denormalized)
        migrations.AddField(
            model_name='transmission',
            name='units_json',
            field=models.JSONField(blank=True, default=list, help_text='Units involved in transmission (denormalized JSON)'),
        ),

        # Change play_length from Float to Decimal for consistency
        migrations.AlterField(
            model_name='transmission',
            name='play_length',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Audio duration in seconds', max_digits=6),
        ),

        # Make slug unique (was just indexed)
        migrations.AlterField(
            model_name='transmission',
            name='slug',
            field=models.UUIDField(default=None, editable=False, unique=True),
        ),

        # Remove unused fields
        migrations.RemoveField(
            model_name='transmission',
            name='audio_file_url_path',
        ),
        migrations.RemoveField(
            model_name='transmission',
            name='audio_file_type',
        ),
        migrations.RemoveField(
            model_name='transmission',
            name='has_audio',
        ),
        migrations.RemoveField(
            model_name='transmission',
            name='from_default_source',
        ),

        # Update indexes for better performance
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['-start_datetime'], name='trans_start_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['talkgroup_info', '-start_datetime'], name='trans_tg_start_idx'),
        ),
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['system', '-start_datetime'], name='trans_sys_start_idx'),
        ),
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['slug'], name='trans_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['emergency', '-start_datetime'], name='trans_emerg_start_idx'),
        ),
        migrations.AddIndex(
            model_name='transmission',
            index=models.Index(fields=['start_datetime', 'system'], name='trans_date_sys_idx'),
        ),

        # Add index to Transcription
        migrations.AddIndex(
            model_name='transcription',
            index=models.Index(fields=['transmission'], name='radio_trans_transmi_idx'),
        ),

        # Update TransmissionUnit indexes
        migrations.AddIndex(
            model_name='transmissionunit',
            index=models.Index(fields=['transmission'], name='radio_trans_trans_idx'),
        ),
        migrations.AddIndex(
            model_name='transmissionunit',
            index=models.Index(fields=['unit'], name='radio_trans_unit_idx'),
        ),

        # Create TransmissionArchive table
        migrations.CreateModel(
            name='TransmissionArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_id', models.BigIntegerField(help_text='Original transmission ID before archiving')),
                ('slug', models.UUIDField()),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField(blank=True, null=True)),
                ('play_length', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('audio_file', models.CharField(max_length=255)),
                ('system_id', models.IntegerField()),
                ('system_name', models.CharField(max_length=100)),
                ('talkgroup_id', models.IntegerField()),
                ('talkgroup_dec_id', models.IntegerField()),
                ('talkgroup_name', models.CharField(max_length=100)),
                ('units_json', models.JSONField(blank=True, default=list)),
                ('freq', models.BigIntegerField(blank=True, null=True)),
                ('emergency', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField()),
                ('archived_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Archived Transmission',
                'verbose_name_plural': 'Archived Transmissions',
                'ordering': ['-start_datetime'],
            },
        ),
        migrations.AddIndex(
            model_name='transmissionarchive',
            index=models.Index(fields=['-start_datetime'], name='radio_trans_start_d_archive_idx'),
        ),
        migrations.AddIndex(
            model_name='transmissionarchive',
            index=models.Index(fields=['talkgroup_id', '-start_datetime'], name='radio_trans_tg_archive_idx'),
        ),
        migrations.AddIndex(
            model_name='transmissionarchive',
            index=models.Index(fields=['system_id', '-start_datetime'], name='radio_trans_sys_archive_idx'),
        ),
        migrations.AddIndex(
            model_name='transmissionarchive',
            index=models.Index(fields=['slug'], name='radio_trans_slug_archive_idx'),
        ),

        # Change Transcription confidence to Decimal
        migrations.AlterField(
            model_name='transcription',
            name='confidence',
            field=models.DecimalField(blank=True, decimal_places=3, help_text='Confidence score for automated transcriptions (0-1)', max_digits=4, null=True),
        ),

        # Change ordering from pk to start_datetime
        migrations.AlterModelOptions(
            name='transmission',
            options={'ordering': ['-start_datetime'], 'permissions': (('download_audio', 'Can download audio clips'),), 'verbose_name': 'Transmission', 'verbose_name_plural': 'Transmissions'},
        ),
    ]
