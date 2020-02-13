
__author__ = "tplick"

from django.db import models
from bakround_applicant.models.db import TimestampedModel
from django.utils import timezone


class SchedulerLastRun(TimestampedModel):
    last_run_date = models.DateTimeField(default=timezone.now, null=False)

    class Meta:
        db_table = "scheduler_last_run"
