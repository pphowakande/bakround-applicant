# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-07 20:51
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bakround_applicant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employer',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=255, null=True)),
                ('gender', models.CharField(blank=True, max_length=16, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('street_address', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=128, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('can_send_email', models.BooleanField(default=False)),
                ('custom_email_body', models.TextField(blank=True, null=True)),
                ('logo_file_name', models.CharField(blank=True, max_length=512, null=True)),
                ('spreadsheet_webhook', models.CharField(blank=True, max_length=100, null=True)),
                ('candidate_queue_enabled', models.BooleanField(default=True)),
                ('auto_contact_enabled', models.BooleanField(default=True)),
                ('short_company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('website_url', models.CharField(blank=True, max_length=255, null=True)),
                ('is_demo_account', models.BooleanField(default=False)),
                ('show_candidates_for_different_job', models.BooleanField(default=False)),
                ('company_description', models.TextField(blank=True, null=True)),
                ('external_contacting_enabled', models.BooleanField(default=False)),
                ('contact_url', models.CharField(blank=True, max_length=255, null=True)),
                ('gh_account_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('gh_api_token', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'employer',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidate',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('contacted', models.BooleanField(default=False)),
                ('responded', models.BooleanField(default=False)),
                ('accepted', models.BooleanField(default=False)),
                ('guid', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('sourced_by_employer', models.BooleanField(default=False)),
                ('visible', models.BooleanField(default=True)),
                ('contacted_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('accepted_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('rejected_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('was_7_day_follow_up_sent', models.BooleanField(db_index=True, default=False)),
                ('decline_reason_comments', models.TextField(blank=True, null=True)),
                ('contacted_externally', models.BooleanField(default=False)),
                ('contact_info_requested', models.BooleanField(default=False)),
                ('was_24_hour_follow_up_sent', models.BooleanField(db_index=True, default=False)),
                ('gh_candidate_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('gh_application_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
            ],
            options={
                'db_table': 'employer_candidate',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidateFeedback',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('bscore_value', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
                ('comment', models.CharField(max_length=10000)),
                ('should_interview', models.BooleanField()),
                ('wrong_job', models.NullBooleanField(db_index=True)),
                ('wrong_language', models.NullBooleanField(db_index=True)),
                ('incomplete', models.NullBooleanField(db_index=True)),
                ('insuff_exp', models.NullBooleanField()),
                ('insuff_skills', models.NullBooleanField()),
                ('insuff_certs', models.NullBooleanField()),
                ('unknown_employers', models.NullBooleanField()),
                ('unknown_schools', models.NullBooleanField()),
                ('feedback_guid', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('candidate_ranking', models.IntegerField(blank=True, null=True)),
                ('actual_bscore', models.DecimalField(decimal_places=2, max_digits=5, null=True)),
            ],
            options={
                'db_table': 'employer_candidate_feedback',
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidateQueue',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('dismissed', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'employer_candidate_queue',
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidateResponse',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('response', models.CharField(max_length=10000)),
            ],
            options={
                'db_table': 'employer_candidate_response',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidateStatus',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'employer_candidate_status',
            },
        ),
        migrations.CreateModel(
            name='EmployerCandidateWebsiteVisited',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'employer_candidate_website_visited',
            },
        ),
        migrations.CreateModel(
            name='EmployerJob',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('job_name', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=128, null=True)),
                ('open', models.BooleanField(default=True)),
                ('guid', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('custom_email_body', models.TextField(blank=True, null=True)),
                ('candidate_queue_enabled', models.BooleanField(default=False)),
                ('auto_contact_enabled', models.BooleanField(default=False)),
                ('visible', models.BooleanField(default=True)),
                ('job_description', models.TextField(blank=True, null=True)),
                ('gh_job_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
            ],
            options={
                'db_table': 'employer_job',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='EmployerJobUser',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'employer_job_user',
            },
        ),
        migrations.CreateModel(
            name='EmployerProfileView',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=128)),
            ],
            options={
                'db_table': 'employer_profile_view',
            },
        ),
        migrations.CreateModel(
            name='EmployerRestrictedProfile',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'employer_restricted_profile',
            },
        ),
        migrations.CreateModel(
            name='EmployerSavedSearch',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('search_parameters', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'db_table': 'employer_saved_search',
            },
        ),
        migrations.CreateModel(
            name='EmployerSearchResult',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('opened', models.BooleanField(db_index=True, default=False)),
            ],
            options={
                'db_table': 'employer_search_result',
            },
        ),
        migrations.CreateModel(
            name='EmployerUser',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('is_billing_admin', models.BooleanField(default=False)),
                ('is_owner', models.BooleanField(default=False)),
                ('jobs_tour_dismissed', models.BooleanField(default=False)),
                ('jobdetail_tour_dismissed', models.BooleanField(default=False)),
                ('search_tour_dismissed', models.BooleanField(default=False)),
                ('custom_email_address', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('auto_contact_enabled', models.BooleanField(default=False)),
                ('linkedin_url', models.CharField(blank=True, max_length=255, null=True)),
                ('daily_summary_email_enabled', models.BooleanField(default=True)),
                ('weekly_stats_email_enabled', models.BooleanField(default=False)),
                ('is_bakround_employee', models.BooleanField(db_index=True, default=False)),
                ('headshot_file_name', models.CharField(blank=True, max_length=255, null=True)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.Employer')),
            ],
            options={
                'db_table': 'employer_user',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='JobRescoreRequest',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Job')),
            ],
            options={
                'db_table': 'job_rescore_request',
            },
        ),
    ]
