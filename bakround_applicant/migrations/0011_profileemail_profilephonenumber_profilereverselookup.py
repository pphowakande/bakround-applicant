# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-17 17:55
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bakround_applicant', '0010_auto_20180814_2134'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileEmail',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('bounces', models.BooleanField(default=False)),
                ('opens', models.BooleanField(default=False)),
                ('responds', models.BooleanField(default=False)),
                ('is_correct_person', models.BooleanField(default=False)),
                ('unsubscribed', models.BooleanField(default=False)),
                ('reported_spam', models.BooleanField(default=False)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProfilePhoneNumber',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('is_correct_person', models.BooleanField(default=False)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProfileReverseLookup',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('provider', models.CharField(max_length=100)),
                ('output', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
