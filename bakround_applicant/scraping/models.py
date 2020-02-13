__author__ = 'ajaynayak'

import tldextract
from django.db import models
from django.contrib.postgres.fields import JSONField
from bakround_applicant.models.db import TimestampedModel, Job, Profile

class ScraperJob(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    start_url = models.TextField(null=False, blank=False, unique=True)
    start_offset = models.IntegerField(blank=False, null=False, default=0)
    running = models.BooleanField(null=False, default=False)
    new_resumes_scraped = models.IntegerField(blank=False, null=False, default=0)
    resumes_rescraped = models.IntegerField(blank=False, null=False, default=0)

    @property
    def source(self):
        return tldextract.extract(self.start_url).domain

    class Meta:
        managed = True
        db_table = 'scraper_job'

class ScraperLogin(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_name = models.CharField(max_length=50, null=False, blank=False)
    password = models.CharField(max_length=50, null=False, blank=False)
    source = models.CharField(max_length=50, null=True, blank=True)
    enabled = models.BooleanField(null=False, blank=False, default=False) 

    # max(total_failures - total_successes, 0)
    # However, when a really bad failure happens, a ScraperLogin may get hit with a +5 or a +10 here.
    adjusted_failure_count = models.IntegerField(blank=False, null=False, default=0)

    class Meta:
        managed = True
        db_table = 'scraper_login'
