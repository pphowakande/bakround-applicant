# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-07 20:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BgAlternateTitles',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=50)),
                ('alt_title', models.TextField(db_index=True)),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_alternate_titles',
            },
        ),
        migrations.CreateModel(
            name='BgOnetAbilities',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_abilities',
            },
        ),
        migrations.CreateModel(
            name='BgOnetCareerChangersMatrix',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('related_onet_id', models.CharField(db_index=True, max_length=45)),
                ('index', models.IntegerField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_career_changers_matrix',
            },
        ),
        migrations.CreateModel(
            name='BgOnetCategory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('category', models.IntegerField(db_index=True)),
                ('category_description', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'bg_onet_category',
            },
        ),
        migrations.CreateModel(
            name='BgOnetKnowledge',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_knowledge',
            },
        ),
        migrations.CreateModel(
            name='BgOnetSkills',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_skills',
            },
        ),
        migrations.CreateModel(
            name='BgOnetTaskRatings',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('task_id', models.CharField(db_index=True, max_length=45)),
                ('task', models.TextField()),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=100)),
                ('category', models.IntegerField(db_index=True)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_task_ratings',
            },
        ),
        migrations.CreateModel(
            name='BgOnetTaskToDwas',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('task_id', models.CharField(db_index=True, max_length=45)),
                ('task', models.TextField()),
                ('dwa_id', models.CharField(db_index=True, max_length=50)),
                ('dwa_title', models.CharField(max_length=255)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_task_to_dwas',
            },
        ),
        migrations.CreateModel(
            name='BgOnetToolsTech',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('t2_type', models.CharField(max_length=255)),
                ('t2_example', models.TextField()),
            ],
            options={
                'db_table': 'bg_onet_tools_tech',
            },
        ),
        migrations.CreateModel(
            name='BgOnetWorkActivities',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_work_activities',
            },
        ),
        migrations.CreateModel(
            name='BgOnetWorkContext',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_work_context',
            },
        ),
        migrations.CreateModel(
            name='BgOnetWorkStyles',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_id', models.CharField(db_index=True, max_length=45)),
                ('element_id', models.CharField(db_index=True, max_length=45)),
                ('element_name', models.CharField(max_length=150)),
                ('scale_id', models.CharField(db_index=True, max_length=20)),
                ('scale_name', models.CharField(max_length=45)),
                ('data_value', models.FloatField()),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_onet_work_styles',
            },
        ),
        migrations.CreateModel(
            name='BgPositionMaster',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('onet_soc_code', models.CharField(db_index=True, max_length=50)),
                ('title', models.TextField(db_index=True)),
                ('description', models.TextField()),
                ('job_family', models.CharField(max_length=255)),
                ('industry_id', models.IntegerField(db_index=True)),
                ('active_status', models.IntegerField()),
            ],
            options={
                'db_table': 'bg_position_master',
            },
        ),
    ]
