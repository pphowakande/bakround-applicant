__author__ = "tplick"

import os
import json
import time
from datetime import datetime, timedelta

from smtpapi import SMTPAPIHeader

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models.expressions import RawSQL
from django.template.loader import render_to_string
from django.utils import timezone

from bakround_applicant.all_models.db import Profile, EmployerUser, EmployerJob, EmployerCandidate, \
                                             EmployerJobUser, EmployerCandidateResponse, Notification, \
                                             Job, JobFamily, ProfileReverseLookup, ProfileEmail, \
                                             EmployerCandidateStatus, Employer, ProfileResume, \
                                             NotificationRecipient
from bakround_applicant.utilities.functions import get_website_root_url, is_production, is_dev
from bakround_applicant.utilities.logger import LoggerFactory
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact

from ..queue import QueueConnection, QueueNames
from .exceptions import UnspecifiedRecipientException, EmailNotFoundException, UnverifiedNameException

logger = LoggerFactory.create("NOTIFICATION_UTIL")

### Generic utilities

def queue_notification(_id, resend=None):
    message = {"notification_id": _id}
    if resend is not None:
        message['resend'] = resend
    QueueConnection.quick_publish(QueueNames.notification_service, json.dumps(message))

def get_bcc_address():
    if is_production():
        return 'bcc@bakround.com'
    elif is_dev():
        return 'bcc-dev@bakround.com'
    else:
        return 'bcc@local'

### Email building utilities

def ensure_recipient_verified(notification):
    """Ensure the recipient profile has been verified. This is to keep bogus names out of email
       we send. Raises UnverifiedNameException()."""
    if notification.recipient_profile and not notification.recipient_profile.name_verification_completed:
        raise UnverifiedNameException(message=None, profile_id=notification.recipient_profile.id)

def get_sender_email(notification, fallback='no-reply@bakround.com'):
    from_email = None
    if notification.sender_profile:
        collect_contact_info_for_profile(notification.sender_profile)
        from_email = ProfileEmail.to_reach(notification.sender_profile_id)
        if from_email:
            from_email = from_email.value

    return from_email or notification.sender_email or fallback

def build_header_json(notification):
    # build the header containing any relevant metadata
    # this is sent back to us by SendGrid via webhook events
    header_json = None
    if notification.metadata is not None:
        metadata = notification.metadata
        if 'bkrnd_nid' not in metadata:
            metadata['bkrnd_nid'] = notification.id
        header = SMTPAPIHeader()
        header.set_unique_args(metadata)
        header_json = {'X-SMTPAPI': header.json_string()}
    return header_json

def get_recipient_email_addresses(notification, resend = False):
    """Given a Notification, return a list of email addresses as strings."""
    all_emails = []

    if notification.recipient_profile:
        collect_contact_info_for_profile(notification.recipient_profile)
        all_emails.extend(ProfileEmail.all_sane().filter(profile_id=notification.recipient_profile.id).values_list("value", flat=True))

    if notification.recipient_email:
        sane_exists = ProfileEmail.all_sane().filter(value=notification.recipient_email).exists()
        exists_generally = ProfileEmail.objects.filter(value=notification.recipient_email).exists()
        if sane_exists or not exists_generally:
            all_emails.append(notification.recipient_email)

    if not all_emails:
        if notification.recipient_profile:
            raise EmailNotFoundException(message="", profile_id=notification.recipient_profile.id)
        else:
            raise UnspecifiedRecipientException()

    return all_emails

### Email sending utilities

def send_email_notification(notification, resend=False):
    # include the original recipients if the service is running in prod, or if it's a system notification
    if is_production() or notification.initiator_user is None:
        ensure_recipient_verified(notification)
        subject = notification.subject
        to_email = get_recipient_email_addresses(notification, resend=resend)

        if notification.follow_up_count > 0:
            subject = "Reminder: {}".format(subject)
    else:
        to_email = [notification.initiator_user.email]
        subject = '{} ({})'.format(notification.subject, ', '.join(to_email))

    from_email = get_sender_email(notification)
    body = notification.html_body or notification.body
    headers = build_header_json(notification)

    for email_address in to_email:
        # TODO: Ensure we don't send emails except from prod
        email = EmailMessage(subject=subject,
                             body=body,
                             from_email=from_email,
                             to=[email_address],
                             bcc=[get_bcc_address()],
                             headers=headers)
        email.content_subtype = "html" # This is an HTML email.
        email.send()

        notification_recipient = NotificationRecipient(notification=notification,
                                                       recipient_email=email.to[0],
                                                       sent=True)
        notification_recipient.save()

    notification.sent = True
    notification.save()

    return to_email


#### High-Level email creation utilities

class FakeEmployerJob:
    def __init__(self, employer):
        self.employer = employer
        self.city = '{CITY}'
        self.state = {"state_code": '{STATE}'}
        self.job_name = '{JOB_NAME}'

def get_default_email_body(employer_job=None, employer=None):
    if employer_job is None:
        employer_job = FakeEmployerJob(employer)

    employer = employer_job.employer

    try:
        employer_user = (EmployerJobUser.objects
                                        .filter(employer_job=employer_job)
                                        .order_by('date_created')
                                        .first()
                                        .employer_user)
    except Exception:
        employer_user = (EmployerUser.objects
                                     .filter(employer=employer,
                                             is_owner=True)
                                     .order_by('date_created')
                                     .first())

    return render_to_string("employer/default_candidate_email_body.html", {
        "employer_job": employer_job,
        "employer_user": employer_user,
        "employer": employer
    })

# TODO: make sure we don't follow up on accepts.
def send_follow_up_emails():
    # Email every candidate contacted at least 2 days ago every
    # day for 5 days, or until they respond.
    # Send a follow-up email if the following conditions are met:
    # 1. employer_candidate.responded = False
    # 2. notification.sent = True for employer_candidate_id
    # 3. notification_recipient.sent = True for notification_id

    two_days_ago = timezone.now() - timedelta(hours=47)
    one_week_ago = timezone.now() - timedelta(hours=24*7)

    for n in (Notification.objects.filter(follow_up_count__lt=7,
                                          employercandidate__responded=False,
                                          sent=True,
                                          initiator_user_id__isnull=False,
                                          date_updated__lte=two_days_ago,
                                          date_updated__gte=one_week_ago)):
        n.follow_up_count += 1
        n.save(update_fields=['follow_up_count'])
        queue_notification(n.id, resend=True)

