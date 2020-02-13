__author__ = 'ajaynayak'

from django.db import models
from bakround_applicant.models.db import TimestampedModel
from bakround_applicant.employer.models import Employer


class LookupPlanLimit(models.Model):
    id = models.AutoField(primary_key=True)
    plan_name = models.CharField(max_length=100, blank=False, null=False)
    action_name = models.CharField(max_length=255, blank=False, null=False)
    limit = models.IntegerField(null=False)

    class Meta:
        db_table = "lookup_plan_limit"


class EmployerTrial(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer = models.ForeignKey(Employer, models.DO_NOTHING, blank=False, null=False)
    trial_days = models.IntegerField(null=False)

    class Meta:
        db_table = "employer_trial"