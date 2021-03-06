# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-14 21:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakround_applicant', '0005_auto_20180724_2038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilecertification',
            name='certification_name',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='profileeducation',
            name='degree_major_other',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profileeducation',
            name='degree_name_other',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='profileeducation',
            name='school_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
