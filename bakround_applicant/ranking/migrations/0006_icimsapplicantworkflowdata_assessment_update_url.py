# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-05-16 17:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0005_icimsjobdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='icimsapplicantworkflowdata',
            name='assessment_update_url',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
