# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-04-05 15:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RankingJob',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('start_date', models.CharField(blank=True, max_length=30, null=True)),
                ('running', models.BooleanField(default=False)),
                ('new_resumes_scraped', models.IntegerField(default=0)),
                ('resumes_rescraped', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'ranking_job',
                'managed': True,
            },
        ),
    ]
