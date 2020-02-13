__author__ = 'ajaynayak'

from django.db import models
from bakround_applicant.users.models import User
from bakround_applicant.models.db import TimestampedModel, Profile, Job, Notification
from django.contrib.postgres.fields import JSONField
import uuid

class Employer(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=16, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    state = models.ForeignKey('lookup.LookupState', models.DO_NOTHING, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    can_send_email = models.BooleanField(default=False)
    custom_email_body = models.TextField(blank=True, null=True)
    logo_file_name = models.CharField(max_length=512, blank=True, null=True)
    job_family = models.ForeignKey('bakround_applicant.JobFamily', models.DO_NOTHING, default=1, null=False, blank=False)
    spreadsheet_webhook = models.CharField(max_length=100, blank=True, null=True)

    candidate_queue_enabled = models.BooleanField(default=True)

    auto_contact_enabled = models.BooleanField(default=True)

    short_company_name = models.CharField(max_length=255, blank=True, null=True)

    industry = models.ForeignKey('lookup.LookupIndustry', models.DO_NOTHING, null=True, blank=True)

    website_url = models.CharField(max_length=255, blank=True, null=True)

    is_demo_account = models.BooleanField(default=False)

    # Normally, when a recruiter contacts a candidate, that candidate will not show up in other searches
    # performed by that employer for two weeks.  To avoid this behavior, set show_candidates_for_different_job
    # to True in the employer's record.
    show_candidates_for_different_job = models.BooleanField(default=False)

    company_description = models.TextField(blank=True, null=True)

    external_contacting_enabled = models.BooleanField(default=False)

    contact_url = models.CharField(max_length=255, blank=True, null=True)

    gh_account_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    gh_api_token = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    def __str__(self):
        return "Employer {} ({})".format(self.id, self.company_name)

    class Meta:
        managed = True
        db_table = 'employer'


class EmployerUser(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer = models.ForeignKey(Employer, models.DO_NOTHING, blank=False, null=False)
    user = models.ForeignKey(User, null=True)
    is_owner = models.BooleanField(default=False)

    is_billing_admin = models.BooleanField(default=False,
                                           null=False,
                                           blank=False)

    is_owner = models.BooleanField(default=False,
                                   null=False,
                                   blank=False)

    jobs_tour_dismissed = models.BooleanField(default=False, null=False, blank=False)
    jobdetail_tour_dismissed = models.BooleanField(default=False, null=False, blank=False)
    search_tour_dismissed = models.BooleanField(default=False, null=False, blank=False)

    custom_email_address = models.CharField(max_length=255, null=True, blank=True, unique=True)

    auto_contact_enabled = models.BooleanField(default=False,
                                               null=False,
                                               blank=False)

    linkedin_url = models.CharField(max_length=255, null=True, blank=True)

    daily_summary_email_enabled = models.BooleanField(default=True)
    weekly_stats_email_enabled = models.BooleanField(default=False)

    is_bakround_employee = models.BooleanField(default=False, db_index=True)

    headshot_file_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "EmployerUser {} (employer id = {}, user id = {})".format(self.id, self.employer_id, self.user_id)

    class Meta:
        managed = True
        db_table = 'employer_user'


class EmployerCandidateResponse(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    response = models.CharField(max_length=10000)

    class Meta:
        managed = True
        db_table = 'employer_candidate_response'


class EmployerJob(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer = models.ForeignKey(Employer, models.DO_NOTHING, blank=False, null=False)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=False, null=False)
    job_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    state = models.ForeignKey('lookup.LookupState', models.DO_NOTHING, blank=True, null=True)
    open = models.BooleanField(default=True)
    guid = models.CharField(max_length=50, blank=True, null=True, unique=True)
    custom_email_body = models.TextField(blank=True, null=True)

    candidate_queue_enabled = models.BooleanField(default=False)
    auto_contact_enabled = models.BooleanField(default=False)

    visible = models.BooleanField(default=True)

    job_description = models.TextField(blank=True, null=True)

    gh_job_id = models.BigIntegerField(blank=True, null=True, db_index=True)

    def __str__(self):
        return "EmployerJob {} (employer id = {}, job id {})".format(self.id, self.employer_id, self.job_id)

    class Meta:
        managed = True
        db_table = 'employer_job'


class EmployerCandidate(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_job = models.ForeignKey(EmployerJob, models.DO_NOTHING, blank=False, null=False, default=None)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, related_name='profiles')
    contacted = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    response = models.ForeignKey(EmployerCandidateResponse, null=True)
    employer_user = models.ForeignKey(EmployerUser, null=True)
    guid = models.CharField(max_length=50, blank=True, null=True, unique=True, default=uuid.uuid4)
    sourced_by_employer = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    notification = models.ForeignKey(Notification, models.DO_NOTHING, blank=True, null=True)

    contacted_date = models.DateTimeField(blank=True, null=True, db_index=True)
    accepted_date = models.DateTimeField(blank=True, null=True, db_index=True)
    rejected_date = models.DateTimeField(blank=True, null=True, db_index=True)

    was_7_day_follow_up_sent = models.BooleanField(default=False, db_index=True)

    employer_candidate_queue = models.ForeignKey('EmployerCandidateQueue', models.DO_NOTHING, blank=True, null=True)

    decline_reason = models.ForeignKey('lookup.LookupDeclineReason', models.DO_NOTHING, blank=True, null=True)
    decline_reason_comments = models.TextField(null=True, blank=True)

    contacted_externally = models.BooleanField(default=False)

    contact_info_requested = models.BooleanField(default=False)

    was_24_hour_follow_up_sent = models.BooleanField(default=False, db_index=True)

    gh_candidate_id = models.BigIntegerField(blank=True, null=True, db_index=True)
    gh_application_id = models.BigIntegerField(blank=True, null=True, db_index=True)

    class Meta:
        managed = True
        unique_together = ("profile", "employer_job")
        db_table = 'employer_candidate'


class EmployerJobUser(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_job = models.ForeignKey(EmployerJob, models.DO_NOTHING, blank=False, null=False)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=False, null=False,
                                      related_name="employer_user")
    added_by = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=True, null=True,
                                 related_name="added_by")

    class Meta:
        db_table = "employer_job_user"
        unique_together = ("employer_job", "employer_user")


class EmployerCandidateStatus(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_candidate = models.ForeignKey(EmployerCandidate, models.DO_NOTHING, blank=False, null=False)
    candidate_status = models.ForeignKey('lookup.LookupCandidateStatus', models.DO_NOTHING, blank=False, null=False)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=False, null=False)
    notes = models.TextField(blank=True, null=True)

    reject_reason = models.ForeignKey('lookup.LookupRejectReason', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = "employer_candidate_status"


class JobRescoreRequest(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=False, null=False)
    created_by = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = "job_rescore_request"


class EmployerSavedSearch(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_job = models.ForeignKey(EmployerJob, models.DO_NOTHING, blank=False, null=False)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=False, null=False)
    search_parameters = JSONField(null=False)

    class Meta:
        db_table = "employer_saved_search"
        indexes = [
            models.Index(fields=['employer_job', 'employer_user', 'id']),
            models.Index(fields=['employer_job', 'id']),
        ]


class EmployerSearchResult(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=False, null=False)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)
    employer_saved_search = models.ForeignKey(EmployerSavedSearch, models.DO_NOTHING, blank=False, null=False)
    opened = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "employer_search_result"
        indexes = [
            models.Index(fields=['employer_saved_search', 'profile']),
        ]


class EmployerCandidateQueue(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_job = models.ForeignKey(EmployerJob, models.DO_NOTHING, blank=False, null=False)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)
    employer_saved_search = models.ForeignKey(EmployerSavedSearch, models.DO_NOTHING, blank=True, null=True)
    dismissed = models.BooleanField(default=False)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = "employer_candidate_queue"
        indexes = [
            models.Index(fields=['dismissed', 'employer_job']),
        ]


class EmployerRestrictedProfile(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer = models.ForeignKey(Employer, models.DO_NOTHING, blank=False, null=False)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)

    class Meta:
        db_table = "employer_restricted_profile"


class EmployerCandidateFeedback(TimestampedModel):
    id = models.BigAutoField(primary_key=True)

    profile = models.ForeignKey(Profile)
    employer_job = models.ForeignKey(EmployerJob)
    employer_user = models.ForeignKey(EmployerUser)

    bscore_value = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    comment = models.CharField(max_length=10000)
    should_interview = models.BooleanField(null=False)

    wrong_job = models.NullBooleanField(db_index=True)
    wrong_language = models.NullBooleanField(db_index=True)
    incomplete = models.NullBooleanField(db_index=True)
    insuff_exp = models.NullBooleanField()
    insuff_skills = models.NullBooleanField()
    insuff_certs = models.NullBooleanField()
    unknown_employers = models.NullBooleanField()
    unknown_schools = models.NullBooleanField()

    feedback_guid = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    saved_search = models.ForeignKey(EmployerSavedSearch, models.DO_NOTHING, blank=True, null=True)
    candidate_ranking = models.IntegerField(blank=True, null=True)

    # the bScore that was shown on the page, as opposed to the score that the reviewer gave us
    actual_bscore = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    class Meta:
        db_table = 'employer_candidate_feedback'


class EmployerProfileView(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_user = models.ForeignKey(EmployerUser, models.DO_NOTHING, blank=False, null=False)
    employer_job = models.ForeignKey(EmployerJob, models.DO_NOTHING, blank=False, null=False)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)
    type = models.CharField(max_length=128)

    class Meta:
        db_table = 'employer_profile_view'
        indexes = [
            models.Index(['employer_user', 'employer_job', 'profile']),
        ]


class EmployerCandidateWebsiteVisited(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    employer_candidate = models.ForeignKey(EmployerCandidate, models.DO_NOTHING)

    class Meta:
        db_table = "employer_candidate_website_visited"
