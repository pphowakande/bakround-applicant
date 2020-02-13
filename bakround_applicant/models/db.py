__author__ = "natesymer"

from django.db import models
from bakround_applicant.users.models import User
from django.contrib.postgres.fields import JSONField

from .timestamped_model import TimestampedModel
from django.forms import widgets
from django.db.models import Q
from bakround_applicant.ranking.models import IcimsJobData

class JobFamily(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    family_name = models.CharField(max_length=255, blank=True, null=True)
    family_description = models.CharField(max_length=10000, blank=True, null=True)
    marketing_site_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_family'


class Job(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job_name = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.CharField(max_length=10000, blank=True, null=True)
    visible = models.BooleanField(default=True)
    parent_job = models.ForeignKey("self", models.DO_NOTHING, blank=True, null=True)
    job_family = models.ForeignKey(JobFamily, models.DO_NOTHING, blank=True, null=True)

    # When an employer customizes a job, the employer will be stored in this field.
    # The job should have its parent_job field point to the original (uncustomized) job.
    employer = models.ForeignKey('employer.Employer', models.DO_NOTHING, blank=True, null=True)

    is_waiting_to_be_scored = models.BooleanField(default=False, blank=False, null=False, db_index=True)
    has_ever_been_scored = models.BooleanField(default=True, blank=False, null=False, db_index=True)

    onet_position = models.ForeignKey('onet.BgPositionMaster', models.DO_NOTHING, blank=True, null=True)

    accuracy = models.IntegerField(blank=True, null=True)

    remap_order = models.IntegerField(blank=True, null=True)
    remap_query = models.TextField(blank=True, null=True)

    last_remap_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Job {} ({})".format(self.id, self.job_name)

    @property
    def remap_queryset(self):
        return (Job.objects
                   .filter(remap_order__isnull=False,
                           remap_query__icontains="SELECT")
                   .order_by('remap_order', 'id'))

    class Meta:
        managed = True
        db_table = 'job'


class JobSkill(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=True, null=True)
    skill = models.ForeignKey('Skill', models.DO_NOTHING, blank=True, null=True)
    default_weightage = models.IntegerField(blank=True, null=True)
    experience_months = models.IntegerField(null=True, default=0)

    class Meta:
        managed = True
        db_table = 'job_skill'


class Profile(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True) # TODO: resolve and deprecate
    gender = models.CharField(max_length=16, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    state = models.ForeignKey('lookup.LookupState', models.DO_NOTHING, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True) # Deprecated, cannot delete
    user = models.ForeignKey(User, null=True)
    job = models.ForeignKey(Job, null=True) # TODO: resolve and deprecate
    linkedin_data = JSONField(null=True) # Has 70 records, maybe delete?
    last_updated_date = models.DateTimeField(blank=True, null=True, db_index=True)
    queued_for_deletion = models.BooleanField(default=False, db_index=True)
    hide_from_search = models.BooleanField(null=False, default=False)
    name_verification_completed = models.BooleanField(null=False, default=False)

    class Meta:
        managed = True
        db_table = 'profile'

class ProfileJobMapping(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, db_index=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=False, null=False, db_index=True)

    class Meta:
        managed = True
        db_table = 'profile_job_mapping'

class IcimsProfileJobMapping(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, db_index=True)
    job = models.ForeignKey(Job, models.DO_NOTHING, blank=False, null=False, db_index=True)
    icims_job_id = models.ForeignKey(IcimsJobData, models.DO_NOTHING, blank=False, null=False, db_index=True)

    class Meta:
        managed = True
        db_table = 'icims_profile_job_mapping'

class ProfileCertification(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)
    certification_name = models.TextField(blank=False, null=False)
    issued_date = models.DateTimeField(blank=True, null=True)
    certification = models.ForeignKey('Certification', blank=False, null=False)

    class Meta:
        managed = True
        db_table = 'profile_certification'


class ProfileResume(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    application_metadata = JSONField(null=True, default={}) # TODO: Maybe we can eliminate this?
    source = models.TextField(blank=True, null=True) # Where the resume came from
    parser_output = JSONField(null=True) # A structured JSON object representing the resume

    def __str__(self):
        return "ProfileResume {} (for profile {})".format(self.id, self.profile_id)

    class Meta:
        managed = True
        db_table = 'profile_resume'


class ProfileEducation(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True)
    school_name = models.TextField(blank=True, null=True)
    school_type = models.TextField(blank=True, null=True)
    degree_name = models.ForeignKey('lookup.LookupDegreeName', models.DO_NOTHING, blank=True, null=True)
    degree_name_other = models.TextField(blank=True, null=True)
    degree_major = models.ForeignKey('lookup.LookupDegreeMajor', models.DO_NOTHING, blank=True, null=True)
    degree_major_other = models.TextField(blank=True, null=True)
    degree_type = models.ForeignKey('lookup.LookupDegreeType', models.DO_NOTHING, blank=True, null=True)
    degree_type_sovren = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    degree_date = models.DateTimeField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.ForeignKey('lookup.LookupState', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'profile_education'


class ProfileExperience(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True)
    company_name = models.TextField(blank=True, null=True)
    position_title = models.TextField(blank=True, null=True)
    position_description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.ForeignKey('lookup.LookupState', models.DO_NOTHING, blank=True, null=True)
    is_current_position = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'profile_experience'


class ProfileSkill(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    skill = models.ForeignKey('Skill', models.DO_NOTHING, blank=False, null=False)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False)
    skill_name = models.TextField(blank=False, null=False)
    experience_months = models.IntegerField(blank=True, null=True)
    last_used_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'profile_skill'


class Skill(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    skill_name = models.TextField(blank=True, null=True, db_index=True)

    def __str__(self):
        return "Skill {} ({})".format(self.id, self.skill_name)

    class Meta:
        managed = True
        db_table = 'skill'


class EmailParseFailures(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job_id = models.BigIntegerField(blank=True, null=True)
    file_name = models.CharField(max_length=512, blank=True, null=True)
    reason = models.CharField(max_length=128, blank=True, null=True)
    application_metadata = JSONField(null=True)

    class Meta:
        managed = True
        db_table = 'email_parse_failures'


class Certification(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    certification_name = models.TextField(blank=True, null=False, db_index=True)
    certification_description = models.TextField(blank=True, null=True)
    parent_certification = models.ForeignKey("self", models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return "Certification {} ({})".format(self.id, self.certification_name)

    class Meta:
        managed = True
        db_table = 'certification'


class JobCertification(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job)
    certification = models.ForeignKey(Certification)
    default_weightage = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_certification'


class ProfileViewer(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True)
    token = models.CharField(max_length=100, null=False, blank=False, unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255)
    notification_sent = models.BooleanField(null=False, default=False)
    active = models.BooleanField(null=False, default=True)

    def __str__(self):
        return "ProfileViewer {} ({})".format(self.id, self.email)

    class Meta:
        managed = True
        db_table = 'profile_viewer'


class ProfileViewerAction(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile_viewer = models.ForeignKey(ProfileViewer, models.DO_NOTHING, blank=True, null=True)
    action_name = models.CharField(max_length=50, null=False, blank=False)

    class Meta:
        managed = True
        db_table = 'profile_viewer_action'

class ProfileVerificationRequest(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.CASCADE, blank=False, null=False)
    callback_queue = models.TextField(blank=True, null=True)
    callback_message = models.TextField(blank=True, null=True)
    use_manual = models.BooleanField(blank=False, null=False, default=False)
    verified = models.BooleanField(blank=False, null=False, default=False)

    metadata = JSONField(default={}, null=False)

    # Did we reach out to the profile on Indeed?
    contacted = models.BooleanField(blank=False, null=False, default=False)
    responded = models.BooleanField(blank=False, null=False, default=False)
    unreachable = models.BooleanField(blank=False, null=False, default=False)

    # Is there something wrong on our end?
    pending_action = models.BooleanField(blank=False, null=False, default=False)
    broken = models.BooleanField(blank=False, null=False, default=False)

    # Did we look up the profile on PIPL?
    lookup_performed = models.BooleanField(blank=False, null=False, default=False)

    class Meta:
        managed = True
        db_table = "profile_verification_request"

class Notification(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=100, null=False, blank=False)
    initiator_user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    sender_profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True, related_name='notification_senders')
    sender_email = models.CharField(max_length=255, null=True, blank=True)
    recipient_profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=True, null=True, related_name='notification_recipients')
    recipient_email = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=512, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    html_body = models.TextField(blank=True, null=True)
    sent = models.BooleanField(null=False, default=False)
    opened = models.BooleanField(null=False, default=False)
    metadata = JSONField(null=True)
    follow_up_count = models.IntegerField(default=0, null=False, blank=False)

    class Meta:
        managed = True
        db_table = 'notification'


class NotificationRecipient(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    notification = models.ForeignKey(Notification, models.DO_NOTHING, blank=True, null=True)
    recipient_email = models.CharField(max_length=255, null=True, blank=True)
    sent = models.BooleanField(null=False, default=False)

    class Meta:
        managed = True
        db_table = 'notification_recipient'


class ProfilePhoneNumber(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, db_index=True)
    value = models.TextField(null=False, blank=False)
    is_correct_person = models.BooleanField(null=False, default=False) # Does this phone number really belong to whom we think?

    @property
    def sane(self):
        return True

    @classmethod
    def all_sane(cls):
        return cls.objects.all()

    @classmethod
    def to_reach(cls, profile_id, strict = False): # Strict has no effect here.
        catchall = []
        is_correct_person = []

        for pe in cls.all_sane().filter(profile_id=profile_id):
            if pe.is_correct_person:
                is_correct_person.append(pe)
            else:
                catchall.append(pe)

        ordered = is_correct_person + catchall
        if len(ordered) > 0:
            return ordered[0]
        return None

    class Meta:
        indexes = [
            models.Index(fields=['value']),
        ]


class ProfileEmail(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, db_index=True)
    value = models.TextField(null=False, blank=False)
    bounces = models.BooleanField(null=False, default=False)
    opens = models.BooleanField(null=False, default=False) # Whether or not the email addr's owner opens our mail.
    responds = models.BooleanField(null=False, default=False) # Whether or not the email addr's owner responds to our mail. Right now, we determine this by if the user clicks a link in the email.
    is_correct_person = models.BooleanField(null=False, default=False) # Does this email address really belong to whom we think?
    unsubscribed = models.BooleanField(null=False, default=False) # Did the user unsubscribe from emails?
    reported_spam = models.BooleanField(null=False, default=False) # Did the user report our emails as spam?

    @property
    def sane(self):
        return not self.bounces and not self.unsubscribed and not self.reported_spam

    @classmethod
    def all_sane(cls):
        return cls.objects.filter(bounces=False, unsubscribed=False, reported_spam=False)
#        return cls.objects.exclude(Q(bounces=True) | Q(unsubscribed=True) | Q(reported_spam=True))

    @classmethod
    def to_reach(cls, profile_id, strict=False):
        catchall = []
        opens = []
        responds = []
        is_correct_person = []

        for pe in cls.all_sane().filter(profile_id=profile_id):
            if pe.is_correct_person:
                is_correct_person.append(pe)
            elif pe.responds:
                responds.append(pe)
            elif pe.opens:
                opens.append(pe)
            elif not strict:
                catchall.append(pe)

        ordered = is_correct_person + responds + opens

        if not strict:
            ordered = ordered + catchall

        if len(ordered) > 0:
            return ordered[0]
        return None

    class Meta:
        indexes = [
            models.Index(fields=['value']),
        ]


class ProfileReverseLookup(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, models.DO_NOTHING, blank=False, null=False, db_index=True)
    provider = models.TextField(null=False, blank=False)
    output = JSONField(null=True)

    @property
    def sanitized_output(self):
        """Due to bugs, some of the ProfileReverseLookup objects
           have a JSON string in `output`"""
        if isinstance(self.output, str):
            self.output = json.loads(self.output)
            self.save(update_fields=['output'])
        return self.output


class IndustryJobFamily(models.Model):
    id = models.BigAutoField(primary_key=True)
    industry = models.ForeignKey('lookup.LookupIndustry')
    job_family = models.ForeignKey(JobFamily)

    class Meta:
        db_table = 'industry_job_family'


#
# DEPRECATED
# These models are still being phased out, and
# will eventually be removed from the database.
#

# replaced by ProfileEmail's bounces field.
class NotificationBouncedEmail(TimestampedModel):
    email = models.CharField(max_length=255, blank=False, null=False, unique=True)

    class Meta:
        managed = True
        db_table = 'notification_bounced_email'

# replaced by ProfileEmail's status fields
class NotificationRecipientEvent(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    notification_recipient = models.ForeignKey(NotificationRecipient, models.DO_NOTHING, blank=True, null=True)
    action = models.CharField(max_length=128, null=False, blank=False)
    sg_event_id = models.CharField(max_length=128, null=True, blank=True)
    metadata = JSONField(null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notification_recipient_event'
        indexes = [
            models.Index(fields=['action', 'email']),
        ]
