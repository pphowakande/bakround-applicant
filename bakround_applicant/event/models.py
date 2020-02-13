
__author__ = "tplick"

from django.db import models
from ..models.timestamped_model import TimestampedModel
from django.contrib.postgres.fields import JSONField


class Event(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('users.User')
    action = models.CharField(max_length=255, null=False, blank=False, db_index=True)
    metadata = JSONField(null=True)

    class Meta:
        db_table = "user_event"
