from django.db import models

class TimestampedModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, null=False)
    date_updated = models.DateTimeField(auto_now=True, null=False)

    class Meta:
        abstract = True

