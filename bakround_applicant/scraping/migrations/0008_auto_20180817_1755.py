# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-17 17:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0007_auto_20180809_2041'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scraperlogin',
            name='has_security_clearance',
        ),
        migrations.AddField(
            model_name='scraperlogin',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
    ]
