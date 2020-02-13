__author__ = 'ajaynayak'

import uuid
import calendar
import json
import string
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from django.db.models.expressions import F, RawSQL, Q
from django.db.models.functions import Coalesce
from django.db.models import DateTimeField, Count
from django.template.loader import render_to_string

from bakround_applicant.notifications import emails
from bakround_applicant.all_models.db import Job, Notification, ProfileEmail, NotificationRecipientEvent, Profile, \
                                             Employer, EmployerUser, EmployerJob, EmployerJobUser, \
                                             EmployerCandidate, EmployerCandidateStatus, EmployerSavedSearch

from bakround_applicant.utilities.functions import get_website_root_url, is_production, is_dev, is_local
from bakround_applicant.utilities.logger import LoggerFactory

from bakround_applicant.event import record_event, EventActions
from bakround_applicant.profile.profile_search import get_location_for_city, make_queryset_of_search_profiles

from bakround_applicant.services.queue import QueueConnection, QueueNames
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile
from bakround_applicant.verifier.utilities import request_verification_for

def get_application_inbox(job_guid):
    root_url = get_website_root_url()

    if root_url is None or 'my.bakround.com' in root_url:
        return 'ejob_{}@applications.bakround.com'.format(job_guid)
    elif 'my-dev.bakround.com' in root_url:
        return 'ejob_{}@applications-dev.bakround.com'.format(job_guid)
    else:
        return 'ejob_{}@applications-local.bakround.com'.format(job_guid)


def replace_tags_in_initial_custom_email(email_body, employer_job):
    if email_body is None:
        return None
    else:
        return (email_body.replace('{JOB_NAME}', employer_job.job_name)
                          .replace('{CITY}', employer_job.city)
                          .replace('{STATE}', employer_job.state.state_code))


def get_logo_image_html(logo_url=None):
    if logo_url is None:
        return None

    return '<img src="{}" style="max-height: 150px; max-width: 150px" />'.format(logo_url)


def generate_custom_email_address(employer_user):
    user = employer_user.user

    if is_production():
        domain = "applications.bakround.com"
    elif is_dev():
        domain = "applications-dev.bakround.com"
    else:
        domain = "local"

    return "{}{}_{}@{}".format(user.first_name.lower().replace(" ", ""),
                               user.last_name.lower().replace(" ", ""),
                               employer_user.id,
                               domain)


def get_jobs_for_employer_user(employer_user):
    return EmployerJob.objects.filter(employerjobuser__employer_user=employer_user).distinct()


def validate_job_location(city, state_code):
    job_location = None
    try:
        job_location = get_location_for_city(city,
                                             state_code)
    except:
        pass

    return job_location is not None


def get_jobs_with_location(employer_id, job_id, city, state, employer_job_ids_to_exclude=None):
    return EmployerJob.objects.filter(employer_id=employer_id,
                                         job_id=job_id,
                                         city=city,
                                         state=state)\
                                    .exclude(id__in=[] if not employer_job_ids_to_exclude else employer_job_ids_to_exclude)


def is_employer_job_location_distinct(employer_id, job_id, city, state, employer_job_ids_to_exclude=None):
    return not get_jobs_with_location(employer_id, job_id, city, state, employer_job_ids_to_exclude)\
        .exists()


def does_closed_job_exist_for_location(employer_id, job_id, city, state, employer_job_ids_to_exclude=None):
    return get_jobs_with_location(employer_id, job_id, city, state, employer_job_ids_to_exclude)\
        .filter(open=False)\
        .exists()

def get_recruiter_for_candidate(candidate):
    if is_production():
        employer_user = candidate.employer_user
        if employer_user is None:
            return get_recruiter_for_job(candidate.employer_job)
        else:
            return employer_user
    else:
        return candidate.employer_user


def full_name_of_employer_user(employer_user):
    user = employer_user.user
    return "{} {}".format(user.first_name, user.last_name)


def get_recruiter_for_job(employer_job):
    employer_job_user = EmployerJobUser.objects.filter(employer_job=employer_job, employer_user__is_bakround_employee=False).first()
    if employer_job_user:
        return employer_job_user.employer_user

    employer_job_user = EmployerJobUser.objects.filter(employer_job=employer_job).first()
    if employer_job_user:
        return employer_job_user.employer_user

    return None


def get_recruiters_list_for_job(employer_job):
    employer_job_user_ids = EmployerJobUser.objects.filter(employer_job=employer_job, employer_user__is_bakround_employee=False).values_list('employer_user_id', flat=True)
    if not employer_job_user_ids:
        return []

    return EmployerUser.objects\
        .filter(id__in=employer_job_user_ids)\
        .order_by('user__first_name', 'user__last_name')\
        .select_related('user')


def get_email_address_for_responding_candidate(candidate):
    # Turning strict on excludes all emails that didn't open emails we sent them.
    collect_contact_info_for_profile(candidate.profile)
    pe = ProfileEmail.to_reach(candidate.profile, strict=True)
    if pe: return pe.value
    return None

def contact_candidate(employer_candidate):
    """If employer_candidate has not already been contacted, send
       them an email and then mark them as contacted. Returns a boolean
       representing whether or not the candidate was contacted by this function."""
    if not employer_candidate.contacted:
        # This code appears to be written by a previous developer
        # because previous EmployerCandidate's didn't have GUID's.
        if not employer_candidate.guid:
            employer_candidate.guid = uuid.uuid4()
            employer_candidate.save()

        emails.ContactCandidate().send(employer_candidate=employer_candidate)

        employer_candidate.contacted = True
        employer_candidate.contacted_date = timezone.now()
        employer_candidate.save()

        record_event(employer_candidate.employer_user.user,
                     EventActions.employer_job_candidate_contact,
                     {"employer_job_id": employer_candidate.employer_job_id,
                      "employer_candidate_id": employer_candidate.id,
                      "profile_id": employer_candidate.profile_id})
        return True
    return False

def handle_candidate_accept(candidate):
    if candidate.responded is False or candidate.accepted is False:
        emails.CandidateAccepted().send(employer_candidate=candidate)

    candidate.responded = True
    candidate.accepted = True

    candidate.save(update_fields=['responded', 'accepted'])

    print("handle_candidate_accept(): Marked EmployerCandidate id {} as accepted.".format(candidate.id))

    if not candidate.accepted_date:
        candidate.accepted_date = timezone.now()
        candidate.save(update_fields=['accepted_date'])

    # if the candidate previously unsubscribed, add their profile back to the search results
    if candidate.profile.hide_from_search:
        profile = candidate.profile
        profile.hide_from_search = False
        profile.save(update_fields=['hide_from_search'])

    print("handle_candidate_accept(): Queuing Profile id {} for re-verification.".format(candidate.profile_id))
    request_verification_for(candidate.profile_id, force_reverification=True)

def handle_candidate_decline(candidate):
    candidate.responded = True
    candidate.rejected_date = timezone.now()
    candidate.accepted = False
    candidate.save()

    print("handle_candidate_decline(): Marked EmployerCandidate id {} as declined.".format(candidate.id))

def handle_candidate_unsubscribe(candidate):
    candidate.responded = True
    candidate.save(update_fields=['responded'])

    profile = employer_candidate.profile
    profile.hide_from_search = True
    profile.save(update_fields=['hide_from_search'])

    QueueConnection.quick_publish(queue_name=QueueNames.on_demand_view_refresher)

def add_candidate_to_job(profile_id, user, employer_job_id, employer_user):
    employer_candidate = EmployerCandidate.objects.filter(employer_job_id=employer_job_id,
                                                          profile_id=profile_id).first()

    if not employer_candidate:
        employer_candidate = EmployerCandidate(employer_job_id=employer_job_id,
                                               profile_id=profile_id,
                                               employer_user=employer_user,
                                               guid=uuid.uuid4())
        employer_candidate.save()

        record_event(employer_user.user,
                     EventActions.employer_job_candidate_add,
                     {"employer_job_id": employer_job_id,
                      "employer_candidate_id": employer_candidate.id,
                      "profile_id": profile_id})
    else:
        if not employer_candidate.visible:
            record_event(employer_user.user,
                         EventActions.employer_job_candidate_add,
                         {"employer_job_id": employer_job_id,
                          "employer_candidate_id": employer_candidate.id,
                          "profile_id": profile_id})

        employer_candidate.visible = True
        employer_candidate.save()

    return employer_candidate

