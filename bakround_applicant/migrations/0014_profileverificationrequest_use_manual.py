# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-29 16:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakround_applicant', '0013_auto_20180829_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileverificationrequest',
            name='use_manual',
            field=models.BooleanField(default=False),
        ),
    ]
