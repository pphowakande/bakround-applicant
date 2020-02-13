
from django.db import models
from ..models.timestamped_model import TimestampedModel


class Score(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey('bakround_applicant.Profile', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey('bakround_applicant.Job', models.DO_NOTHING, blank=True, null=True)
    score_value = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)
    algorithm_version = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'score'

Score._meta.get_field('date_created').db_index = True
Score._meta.get_field('job_id').db_index = True
Score._meta.get_field('profile_id').db_index = True

class ScoreRequest(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey('bakround_applicant.Profile', models.DO_NOTHING, blank=True, null=True)
    job = models.ForeignKey('bakround_applicant.Job', models.DO_NOTHING, blank=True, null=True)
    score = models.ForeignKey(Score, null=True)
    user_generated = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'score_request'

