# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-23 20:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0002_auto_20181022_1945'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='score',
            name='profile_detail',
        ),
        migrations.RemoveField(
            model_name='scorerequest',
            name='profile_detail',
        ),
    ]
