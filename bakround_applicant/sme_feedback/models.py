
# tplick, 4 Jan 2017

from django.db import models
from bakround_applicant.models.db import TimestampedModel, Profile, Job, ProfileResume
from bakround_applicant.users.models import User
from datetime import datetime
from django.utils import timezone


class SME(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job, null=True)
    guid = models.CharField(max_length=100, null=False, blank=False, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    review_limit = models.IntegerField(null=True)
    active = models.BooleanField(null=False, default=True)

    region = models.ForeignKey('lookup.LookupRegion', models.DO_NOTHING, blank=True, null=True)

    ask_about_low_scores = models.BooleanField(default=True)

    employer_user = models.ForeignKey('employer.EmployerUser', models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return "SME {} ({} {})".format(self.id, self.first_name, self.last_name)

    class Meta:
        managed = True
        db_table = 'sme'


class SMEFeedback(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    sme = models.ForeignKey(SME)
    profile_resume = models.ForeignKey(ProfileResume, null=True)
    bscore_value = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    comment = models.CharField(max_length=10000)
    should_interview = models.BooleanField(null=False)
    sme_pay_rate = models.ForeignKey('SMEPayRate', null=True)

    # These values come from the checkboxes on the SME Feedback page.
    # Three columns are indexed because we may search on those columns
    # in the resume-retrieval query.
    wrong_job = models.NullBooleanField(db_index=True)
    wrong_language = models.NullBooleanField(db_index=True)
    incomplete = models.NullBooleanField(db_index=True)
    insuff_exp = models.NullBooleanField()
    insuff_skills = models.NullBooleanField()
    insuff_certs = models.NullBooleanField()
    unknown_employers = models.NullBooleanField()
    unknown_schools = models.NullBooleanField()

    feedback_guid = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    class Meta:
        managed = True
        db_table = 'sme_feedback'


class SMEPayRate(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    sme = models.ForeignKey(SME)
    pay_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0)
    effective_date = models.DateTimeField(default=timezone.now, null=False)

    class Meta:
        managed = True
        db_table = 'sme_pay_rate'


class SMEAction(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    sme = models.ForeignKey(SME)
    profile_resume = models.ForeignKey(ProfileResume, null=True)
    action_name = models.CharField(max_length=50, null=False, blank=False)

    class Meta:
        managed = True
        db_table = 'sme_action'
