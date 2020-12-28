# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-05 17:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dec_id', models.IntegerField(unique=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]