__author__ = 'poonam'

import tldextract
from django.db import models
from django.contrib.postgres.fields import JSONField
from bakround_applicant.models.db import TimestampedModel

class RankingJob(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    start_date = models.CharField(max_length=30, blank=True, null=True)
    start_offset = models.IntegerField(blank=False, null=False, default=0)
    running = models.BooleanField(null=False, default=False)
    new_resumes_scraped = models.IntegerField(blank=False, null=False, default=0)
    resumes_rescraped = models.IntegerField(blank=False, null=False, default=0)

    @property
    def source(self):
        return "icims"

    class Meta:
        managed = True
        db_table = 'ranking_job'

class ICIMSLastUpdatedDate(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    last_updated_date = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'icims_last_updated_date'


class ICIMSApplicantWorkflowData(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=100, blank=True, null=True)
    workflow_id = models.BigIntegerField(blank=False, null=False)
    workflow_url = models.CharField(max_length=255, blank=False, null=False)
    person_id = models.BigIntegerField(blank=False, null=False)
    person_name = models.CharField(max_length=255, blank=False, null=False)
    person_url = models.CharField(max_length=255, blank=False, null=False)
    job_url = models.CharField(max_length=255, blank=True, null=True)
    is_scored = models.BooleanField(default=False)
    assessment_update_url = models.CharField(max_length=255, blank=True, null=False)

    class Meta:
        managed = True
        db_table = 'icims_applcnt_workflow_data'


class IcimsJobData(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job_link = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'icims_job_data'
