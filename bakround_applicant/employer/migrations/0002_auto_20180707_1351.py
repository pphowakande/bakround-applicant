# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-07 20:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employer', '0001_initial'),
        ('lookup', '0001_initial'),
        ('bakround_applicant', '0002_auto_20180707_1351'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='employeruser',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='employersearchresult',
            name='employer_saved_search',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerSavedSearch'),
        ),
        migrations.AddField(
            model_name='employersearchresult',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employersearchresult',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employersavedsearch',
            name='employer_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employersavedsearch',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employerrestrictedprofile',
            name='employer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.Employer'),
        ),
        migrations.AddField(
            model_name='employerrestrictedprofile',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employerprofileview',
            name='employer_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employerprofileview',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employerprofileview',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employerjobuser',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='added_by', to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employerjobuser',
            name='employer_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employerjobuser',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='employer_user', to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employerjob',
            name='employer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.Employer'),
        ),
        migrations.AddField(
            model_name='employerjob',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Job'),
        ),
        migrations.AddField(
            model_name='employerjob',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupState'),
        ),
        migrations.AddField(
            model_name='employercandidatewebsitevisited',
            name='employer_candidate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerCandidate'),
        ),
        migrations.AddField(
            model_name='employercandidatestatus',
            name='candidate_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupCandidateStatus'),
        ),
        migrations.AddField(
            model_name='employercandidatestatus',
            name='employer_candidate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerCandidate'),
        ),
        migrations.AddField(
            model_name='employercandidatestatus',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employercandidatestatus',
            name='reject_reason',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupRejectReason'),
        ),
        migrations.AddField(
            model_name='employercandidatequeue',
            name='employer_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employercandidatequeue',
            name='employer_saved_search',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerSavedSearch'),
        ),
        migrations.AddField(
            model_name='employercandidatequeue',
            name='employer_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employercandidatequeue',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employercandidatefeedback',
            name='employer_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employercandidatefeedback',
            name='employer_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employercandidatefeedback',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employercandidatefeedback',
            name='saved_search',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerSavedSearch'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='decline_reason',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupDeclineReason'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='employer_candidate_queue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerCandidateQueue'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='employer_job',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='employer.EmployerJob'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='employer_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='employer.EmployerUser'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='notification',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.Notification'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='profiles', to='bakround_applicant.Profile'),
        ),
        migrations.AddField(
            model_name='employercandidate',
            name='response',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='employer.EmployerCandidateResponse'),
        ),
        migrations.AddField(
            model_name='employer',
            name='industry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupIndustry'),
        ),
        migrations.AddField(
            model_name='employer',
            name='job_family',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, to='bakround_applicant.JobFamily'),
        ),
        migrations.AddField(
            model_name='employer',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='lookup.LookupState'),
        ),
        migrations.AddIndex(
            model_name='employersearchresult',
            index=models.Index(fields=['employer_saved_search', 'profile'], name='employer_se_employe_2308e0_idx'),
        ),
        migrations.AddIndex(
            model_name='employersavedsearch',
            index=models.Index(fields=['employer_job', 'employer_user', 'id'], name='employer_sa_employe_92adec_idx'),
        ),
        migrations.AddIndex(
            model_name='employersavedsearch',
            index=models.Index(fields=['employer_job', 'id'], name='employer_sa_employe_ac7853_idx'),
        ),
        migrations.AddIndex(
            model_name='employerprofileview',
            index=models.Index(fields=['employer_user', 'employer_job', 'profile'], name='employer_pr_employe_f192df_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='employerjobuser',
            unique_together=set([('employer_job', 'employer_user')]),
        ),
        migrations.AddIndex(
            model_name='employercandidatequeue',
            index=models.Index(fields=['dismissed', 'employer_job'], name='employer_ca_dismiss_a6093a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='employercandidate',
            unique_together=set([('profile', 'employer_job')]),
        ),
    ]
