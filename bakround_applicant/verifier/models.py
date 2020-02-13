__author__ = "natesymer"

from django.db import models
from bakround_applicant.models.db import TimestampedModel
from django.contrib.postgres.fields import JSONField

class ExternalResponse(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    received = models.DateTimeField(blank=False, null=False, db_index=True)
    from_email = models.TextField(blank=False, null=True)
    to_email = models.TextField(blank=False, null=True)
    body = models.TextField(blank=False, null=True)
    metadata = JSONField(null=False, blank=False, default={})
    source = models.TextField(blank=False, null=False, db_index=True)
    processed = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'external_response'
