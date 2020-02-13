__author__ = 'natesymer'

"""
verifyingservice

see $PROJECT_ROOT/bakround_applicant/verifier/readme.md

This service is designed to be invoked as an ancillary step in invoking another service.

i.e. You need to send someone an email, but don't have an email.

In such a case, you'd use the callback_{queue,message} parameters to specify which queue should be called
after a successful verification. These values are persisted; even if verification fails, so that one day, if they're manually verified, the callback queue message will be queued.

Message structure:
{ 'profile_id': 638605, 'callback_queue': 'my_queue', 'callback_message': bytes() } 

Messages are json-encoded dicts. `profile_id` is required. `callback_{queue,message}` are optional.
"""

import uuid
import json
import os
from datetime import timedelta, datetime

from django.utils.html import strip_tags

from ..base import BaseConsumer, FatalException
from .util import collect_contact_info_for_profile, add_contact, verify_sane
from bakround_applicant.browsing.util import indeed_re_scrape, indeed_external_contact
from bakround_applicant.browsing import *
from bakround_applicant.browsing.actions.indeed.contact import IndeedMessage
from bakround_applicant.verifier.lookup_brokers import PiplLookupBroker, AmbiguousLookupException, \
                                                       UnexpectedOutputException, LookupFailedException
from bakround_applicant.services.queue import QueueNames
from bakround_applicant.all_models.db import Profile, ProfileResume, ProfileEmail, ProfileResume, \
                                             ProfilePhoneNumber, ProfileVerificationRequest, \
                                             ScraperLogin, EmployerCandidate
from bakround_applicant.services.notificationservice.util import get_default_email_body
from bakround_applicant.utilities.functions import is_production
from bakround_applicant.services.buildprofile.consumer import Consumer as BuildProfileConsumer

class Consumer(BaseConsumer):
    service_name = 'VERIFYING_SVC'
    queue_name = QueueNames.verifying_service

    def handle_message(self, body):
        message = json.loads(body)

        force_reverification = message.get('force_reverification') or False
        
        request_id = message.get('request_id')
        if not request_id:
            raise ValueError("Missing ProfileVerificationRequest id (request_id)")

        request = ProfileVerificationRequest.objects.filter(id=int(request_id)).first()
        if not request:
            raise ValueError("ProfileVerificationRequest id {} does not exist.".format(request_id))

        if request.use_manual and not force_reverification:
            self.logger.info("ProfileVerificationRequest id {}'s use_manual = True. Exiting.".format(request_id))
            return

        profile = request.profile
        collect_contact_info_for_profile(profile)

        if not profile.name_verification_completed or force_reverification:
            if rescrape_authenticated(profile):
                self.logger.info("Successfully re-scraped Profile id {}.".format(profile.id))
                profile.name_verification_completed = True
                profile.save()
            else:
                self.logger.info("Failed to re-scrape Profile id {} authenticated.".format(profile.id))

        if (profile.name_verification_completed and not ProfileEmail.to_reach(profile.id)) or force_reverification:
            if lookup_profile(profile, use_cache=not force_reverification):
                self.logger.info("Successful external lookup for Profile id {}!".format(profile.id))
            else:
                self.logger.info("Unsuccessful external lookup for Profile id {}.".format(profile.id))

        if not profile.name_verification_completed or not ProfileEmail.to_reach(profile.id):
            self.logger.info("Failed to find sufficient information for ProfileVerificationRequest id {} (Profile id {}).".format(request.id, request.profile.id))
            request.use_manual = True
            request.save()

            # natesymer 11.15.18 - Stop using a headless browser to contact people on Indeed.
            #                      It gets our accounts banned.
            # if not request.contacted:
            #     message = get_message_for(request)
                
            #     if not message:
            #         self.logger.info("ProfileVerificationRequest id {} didn't have necessary metadata to contact through Indeed.".format(request.id))
            #     elif is_production():
            #         # TODO: this is hardcoded for expedience. Generalize.
            #         self.logger.info("Attempting external contact via Indeed.")
            #         user_name = os.environ.get("INDEED_EMAIL", default="admin@bakround.com")
            #         try:
            #             scraper_login = ScraperLogin.objects.get(user_name=user_name, source='indeed')
            #             not_already_contacted = indeed_external_contact(profile, message, scraper_login).result
            #             if not_already_contacted:
            #                 self.logger.info("Sucessfully contacted Profile id {} via Indeed".format(profile.id))
            #             else:
            #                 self.logger.info("We've already contacted Profile id {} via Indeed.".format(profile.id))
            #             request.contacted = True
            #             request.save()
            #         except ScraperLogin.DoesNotExist:
            #             self.logger.error("No ScraperLogin exists with the username {}. Check your INDEED_EMAIL environment variable.".format(user_name))
            #         except (BrowserActionFatalError, BrowserFatalError):
            #             self.logger.error("Encountered fatal error from the browsing infrastructure:\n", exc_info=True)
            #     else:
            #         self.logger.info("Not contacting because we're not in production!")

            self.logger.info("Falling back to manual.")
            return

        # TODO: Phone number validation here - use a service.

        self.logger.info("Successfully automatically verified ProfileVerificationRequest id {} (Profile id {})".format(request.id, profile.id))
        request.verified = True
        request.save()

        if request.callback_queue and request.callback_message:
            self.send_message(request.callback_queue, request.callback_message)

def strip_lines_and_tags(string):
    return strip_tags('\n'.join(map(lambda x: x.rstrip(), filter(bool, string.splitlines()))))

def get_message_for(pfl_verif_request):
    ecid_orig = pfl_verif_request.metadata.get("bkrnd_ecid")
    if not ecid_orig:
        print("get_message_for(): No ecid")
        return None

    try:
        ecid = int(ecid_orig)
    except:
        print("get_message_for(): INVALID METADATA `bkrnd_ecid`: {}".format(ecid_orig))
        return None

    print("get_message_for(): Found employer candidate ID:", ecid)

    employer_candidate = EmployerCandidate.objects.filter(id=ecid).first()
    if not employer_candidate:
        print("get_message_for(): EmployerCandidate id {} doesn't exist.".format(ecid))
        return None

    if not employer_candidate.guid:
        employer_candidate.guid = uuid.uuid4()
        employer_candidate.save()

    print("get_message_for(): Found EmployerCandidate id {}".format(employer_candidate.id))

    recruiter = employer_candidate.employer_user
    if not recruiter:
        print("get_message_for(): No recruiter")
        return None

    print("get_message_for(): Building message to EmployerCandidate id {}".format(employer_candidate.id))

    job = employer_candidate.employer_job

    msg = IndeedMessage()
    msg.recruiter_name = recruiter.user.name
    msg.company_name = recruiter.employer.company_name
    msg.job_title = job.job_name or job.job.job_name
    msg.job_description = "{}\n\nFor internal use (do not delete): {}".format(job.job_description or job.job.job_description, employer_candidate.guid)
    msg.message = "{CANDIDATE_NAME},\n\n" + (strip_lines_and_tags(job.custom_email_body or get_default_email_body(employer_job=job)) or "")
    return msg

def lookup_profile(profile, require_emails=False, require_phones=False, require_addresses=False, use_cache=True):
    broker = PiplLookupBroker(profile=profile, require_emails=require_emails, require_phones=require_phones, require_addresses=require_addresses, use_cache=use_cache)
    try:
        broker.preload()
        found_phone = False
        for phone_number in broker.phones:
            found_phone = found_phone or add_contact(ProfilePhoneNumber, phone_number, profile.id).sane
        
        found_email = False
        for email_address in broker.emails:
            found_email = found_email or add_contact(ProfileEmail, email_address, profile.id).sane
        
        success = True
        if require_emails: success = success and found_email
        if require_phones: success = success and found_phone

        if broker.gender:
            profile.gender = broker.gender
            profile.save()

        # TODO: when a profile is capable of having multiple addresses, let's do this.
        if broker.addresses:
            profile.address = broker.addresses[0]["street_address"]

        return success
    except LookupFailedException:
        print("LookupFailedException")
        return False
    except UnexpectedOutputException:
        print("UnexpectedOutputException")
        return False
    except AmbiguousLookupException:
        print("AmbiguousLookupException")
        return False
    return True

def rescrape_authenticated(profile):
    # Find the latest resume and re-scrape it authenticated.
    profile_resume = ProfileResume.objects.filter(profile_id=profile.id).order_by("-date_created").first()

    if not profile_resume:
        print("rescrape_authenticated(): failed to find resume for Profile id {}.".format(profile.id))
        return False

    succeeded = True

    def on_resume(profile_data, url):
        # Save what we scraped
        auth_pr = ProfileResume(
            url=url,
            source=profile_resume.source,
            parser_output=profile_data,
            profile=profile
        )
        auth_pr.save()

        # Call the profile builder service's logic
        # we don't want to maintain two different implementations
        build_profile = BuildProfileConsumer()
        pd_model = build_profile.load_resume_data(auth_pr)
        build_profile.update_profile_record_from_resume(profile, pd_model, True)

        # If we successfully verified the name of the profile,
        # verification is a success. Otherwise, it failed.
        return profile.name_verification_completed

    try:
        if profile_resume.source == "indeed":
            indeed_re_scrape(profile_resume, on_resume)
        else:
            raise FatalException("Unknown source {}.".format(profile_resume.source))
    except (BrowserFatalError, BrowserActionFatalError) as e:
        print("rescrape_authenticated(): failed to re-scrape profile id {}".format(profile.id))
        return False

    return True

