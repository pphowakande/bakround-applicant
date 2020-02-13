# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-09-24 15:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0009_auto_20180828_2122'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scraperjob',
            name='end_page',
        ),
        migrations.RemoveField(
            model_name='scraperjob',
            name='priority',
        ),
        migrations.AlterField(
            model_name='scraperjob',
            name='start_url',
            field=models.TextField(unique=True),
        ),
    ]
