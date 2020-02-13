__author__ = "natesymer"

from django.conf import settings

from ..factory import NotificationFactory
from bakround_applicant.utilities.functions import get_website_root_url
from bakround_applicant.services.notificationservice.util import get_default_email_body
from bakround_applicant.all_models.db import ProfileReverseLookup, ProfileEmail, ProfilePhoneNumber

class ContactCandidate(NotificationFactory):
    """This is the first email we send to a candidate."""

    def pick_template(self, *args, **kwargs):
        return "email/new_candidate_email.html"

    def generate_metadata(self, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        # Help associate emails with candidates
        return {
            "bkrnd_ecid": employer_candidate.id,
            "bkrnd_ejid": employer_candidate.employer_job_id,
            "bkrnd_euid": employer_candidate.employer_user_id,
            "bkrnd_url": get_website_root_url()
        }

    def generate_context(self, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        employer_job = employer_candidate.employer_job
        employer = employer_job.employer
        if employer_job.custom_email_body and employer_job.custom_email_body.strip():
            email_body = employer_job.custom_email_body
        else:
            email_body = get_default_email_body(employer_job=employer_job)
        
        # grab the url that the Bakround logo should point to
        bakround_logo_url = None
        current_job = employer_job.job
        if current_job.job_family:
            bakround_logo_url = current_job.job_family.marketing_site_url
        if not bakround_logo_url:
            bakround_logo_url = 'http://www.bakround.com'
        
        root_url = get_website_root_url()
        cand_guid = employer_candidate.guid
        
        context = {
            "candidate": employer_candidate.profile,
            "employer_user": employer_candidate.employer_user,
            "employer_job": employer_job,
            "employer": employer,
            "accept_url": "{}/candidate/accept/{}".format(root_url, cand_guid),
            "decline_url": "{}/candidate/decline/{}".format(root_url, cand_guid),
            "email_body": email_body,
            "unsubscribe_url":  "{}/unsubscribe/{}".format(root_url, cand_guid),
            "bakround_logo_url": bakround_logo_url,
            "recruiter": employer_candidate.employer_user.user,
            "employer_website_url": "{}/company_website_redirect/{}".format(root_url, cand_guid)
        }
        
        if employer_job.employer.logo_file_name:
            context["employer_logo_url"] = "{}{}".format(settings.MEDIA_URL, employer.logo_file_name)

        return context

    def postprocess(self, n, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        recruiter = employer_candidate.employer_user

        sender = '{} {} <{}>'.format(recruiter.user.first_name, recruiter.user.last_name, recruiter.custom_email_address)

        n.sender_email = sender
        n.initiator_user_id = recruiter.user_id

        if recruiter.employer.can_send_email:
            n.recipient_profile_id = employer_candidate.profile_id
        else:
            n.recipient_email = str(recruiter.user.email)

        return n

    def after_send(self, n, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        employer_candidate.notification = n
        employer_candidate.save()

class CandidateUpdatedInfo(NotificationFactory):
    """This email notification is sent to a recruiter when one of
    their candidates updates their information."""
    def pick_template(self, *args, **kwargs):
        return "email/candidate_has_updated_info.html"

    def generate_context(self, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        return {
            "candidate": employer_candidate,
            "profile": employer_candidate.profile,
            "recruiter": employer_candidate.employer_user,
            "candidate_status_url": "{}/employer/candidate_status_detail/{}".format(get_website_root_url(),
                                                                               employer_candidate.id),
            "profile_pdf_url": "{}/profile/pdf/{}?bkgen=1&ejid={}".format(get_website_root_url(),
                                                                     employer_candidate.profile_id,
                                                                     employer_candidate.employer_job_id)
        }

    def postprocess(self, n, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        n.sender_email = "no-reply@bakround.com"
        n.recipient_email = employer_candidate.employer_user.user.email
        return n

# TODO: send an email to multiple recipients
#         recipients = [str(employer_job_user.employer_user.user.email)
#                       for employer_job_user
#                       in EmployerJobUser.objects.filter(employer_job=employer_candidate.employer_job)]
class CandidateAccepted(NotificationFactory):
    """The candidate clicked the `Accept` link"""

    def pick_template(self, *args, **kwargs):
        return "notifications/notification_to_recruiter.html"

    def generate_context(self, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        emails = ProfileEmail.all_sane().filter(profile_id=employer_candidate.profile_id).values_list('value', flat=True)
        phones = ProfilePhoneNumber.all_sane().filter(profile_id=employer_candidate.profile_id).values_list('value', flat=True)

        context = {
            "candidate": employer_candidate.profile,
            "employer_user": employer_candidate.employer_user,
            "job": employer_candidate.employer_job.job,
            "employer_job": employer_candidate.employer_job,
            "view_profile_url": "{}/profile/pdf/{}?bkgen=1".format(get_website_root_url(), employer_candidate.profile.id),
            "candidate_status_url": "{}/employer/candidate_status_detail/{}".format(get_website_root_url(), employer_candidate.id),
            "email_addresses": emails,
            "phone_numbers": phones,
            "website_root_url": get_website_root_url()
        }

        if employer_candidate.response:
            context['candidate_response'] = employer_candidate.response.response
        
        return context

    def postprocess(self, n, *args, **kwargs):
        employer_candidate = kwargs.get('employer_candidate')
        if not employer_candidate:
            raise ValueError("Missing keyword argument: employer_candidate")

        n.recipient_email = employer_candidate.employer_user.user.email
        n.sender_email = 'no-reply@bakround.com'
        return n

