__author__ = "natesymer"

import os
import re
import json

from .email import Mailbox, EmailMessage, IMAPError
from .models import ExternalResponse

from bakround_applicant.utilities.logger import LoggerFactory
from bakround_applicant.employer.utils import handle_candidate_accept
from bakround_applicant.all_models.db import EmployerCandidate

# Right now, this only watches Gmail for new emails and saves them.
#
# Indeed will send us an email with X-Indeed-Content-Type: contacted-decline from `do-not-reply@indeed.com` when a candidate rejects.
# Indeed will send us an email to *@indeedemail.com when a candidate accepts.

logger = LoggerFactory.create("watch_for_indeed_emails()")

GUID_REGEX = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')
def find_guid(s):
    if not s:
        return None

    global GUID_REGEX
    employer_candidate_id = list(GUID_REGEX.findall(s)) or None
    if employer_candidate_id:
        employer_candidate_id = employer_candidate_id[-1] or None

    return employer_candidate_id

# def get_rejected_since():
#     previous_response = ExternalResponse.objects.filter(metadata__content_type='contacted-decline').order_by('-received').first()
#     if previous_response:
#         since = previous_response.received
#         logger.debug("Using since date (accepted): {}".format(since))
#         return since
#     return None

def get_accepted_since():
    previous_response = ExternalResponse.objects.exclude(metadata__content_type='contacted-decline').order_by('-received').first()
    if previous_response:
        since = previous_response.received
        logger.debug("Using since date (rejected): {}".format(since))
        return since
    return None

def watch_for_indeed_emails():
    if "INDEED_IMAP_EMAIL" not in os.environ:
        print("Missing INDEED_IMAP_EMAIL environment variable.")
        return

    try:
        inbox = Mailbox(username=os.getenv("INDEED_IMAP_EMAIL"),
                        password=os.getenv("INDEED_IMAP_PASSWORD"),
                        host=os.getenv("INDEED_IMAP_HOST", default="imap.gmail.com"),
                        port=int(os.getenv("INDEED_IMAP_PORT", default="993")))
        
        if inbox.authenticate():
            # Accepts emails sent to addresses like `vanessacoley7_ize@indeedemail.com`
            for x in inbox.messages(from_email="indeedemail.com", since=get_accepted_since()):
                resp = ExternalResponse(received=x.received, body=x.text, to_email=x.to_email, from_email=x.from_email, metadata=x.indeed_metadata, source="indeed_response_email")
                resp.save()
                logger.info("Saved ExternalResponse id {} (from {}).".format(resp.id, x.from_email))

                if not x.text:
                    logger.debug("Empty email message!")
                    continue

                # We embed a GUID after the job description. Find it.
                employer_candidate_guid = find_guid(resp.body)
                if employer_candidate_guid:
                    logger.info("Found EmployerCandidate GUID in email: {}".format(employer_candidate_guid))
                    ec = EmployerCandidate.objects.filter(guid=employer_candidate_guid).first()
                    if ec:
                        # TODO: find all URLs in `resp.body` and see if any of them has a resume attached
                        #       to them that has a matching profile id to our employer candidate.
                        handle_candidate_accept(ec)
                else:
                    logger.debug("No EmployerCandidate GUID.")

            #for x in inbox.messages(header=["X-Indeed-Content-Type", "contacted-decline"]):
            #    pass
                    
        else:
            logger.error("Failed to authenticate with {}.".format(inbox.username))
    except IMAPError as e:
        logger.error("Failed to get email messages. Status Code={}, Phase={}".format(e.status_code, e.phase))

