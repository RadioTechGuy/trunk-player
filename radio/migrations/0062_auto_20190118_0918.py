# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-18 17:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0061_transmission_has_audio'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecorderPC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(db_index=True, max_length=20)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='transmission',
            name='recorder_device',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='transmission',
            name='recorder_pc',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='radio.RecorderPC'),
        ),
    ]
