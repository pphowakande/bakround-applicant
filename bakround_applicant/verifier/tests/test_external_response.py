__author__ = "natesymer"

import pytest
import json
import uuid
from bakround_applicant.all_models.db import *
from bakround_applicant.verifier.email_watcher import find_guid
from bakround_applicant.services.verifyingservice.consumer import *

TEST_INDEED_ACCEPT_RESPONSE = """
LaShawn Herod's resume with contact details:\r\nhttps://www.indeed.com/r/80238cf9870361ae\r\n\r\nI am interested in the position as a CNA ! Can you please contact me with all the information please thanks.\r\n\r\n\r\nOn Sun, Oct 7, 2018 at 05:14 PM -05:00, Kate Bingham wrote:\r\n\r\n> Reminder: this email from Kate Bingham is awaiting your response\r\n> ---\r\n> LaShawn Herod, \r\n> \r\n> I found your resume on Indeed and am recruiting for a CNA role with \r\n> Senior Helpers.  Your resume appears to be a good fit, is this a role you \r\n> maybe interested in learning more about?\r\n> \r\n> JOB DETAILS\r\n> Job Title: CNA\r\n> Company: Senior Helpers\r\n> \r\n> The CNA candidate must be a licensed CNA in the State of California and \r\n> has worked as a CNA for minimum one year. \r\n> Internal candidate tracking ID: {}\r\n> \r\n> Join an orga8359y23 482934yb28934nization of dedicated professionals who are committed to \r\n> excellence in the provision of care at home.  Senior Helpers offers an \r\n> excellent pay rate and work opportunities.Unsubscribe from future \r\n> reminders for this contact: \r\n> https://resumecontacts.indeed.com/reminder/unsubscribe?cotk=1cot4d9662tm98\r\n0i&remtk=1cp89hv0r390g801\r\n\r\n\r\nSuspect spam or fraud?\r\nReport this message to Indeed <https://m.indeedemail.com/report-email?info=u2hVEpbyaM_6bahviabqoxCHFQXHDrmoaswBWTDZBXBE6NlvLPtLACCPlfXtpuc0MTxWMmBqYzsPaX9kcqPECSs-kBr3ghV67MpcHqkfhO3hKuFKavbYR4F6wRPGBKEm5I-1Y-NAo1MiUwIrrIQzzv3pimroJz3mGE7vGftMjm1WWHYWgGY_vSjbjhagaAZ7bFFC193Dzj7zqDGAmtkvJ6y7K7Xv51JJ2ptO9XQp9EJM07Rj2bUSUnAkZFMZIsyVVbZb>\r\n\r\nBy replying or using an indeedemail.com email address, you agree that this email will be processed and analyzed according to the Indeed Cookie Policy <https://www.indeed.com/legal?hl=en&amp;co=US#cookies>, Privacy Policy <https://www.indeed.com/legal?hl=en&amp;co=US#privacy>, and Terms of Service <https://www.indeed.com/legal?hl=en&amp;co=US#tos>.
"""

#@pytest.mark.django_db
def test_find_guid(capsys):
    global TEST_INDEED_ACCEPT_RESPONSE
    guid = str(uuid.uuid4())

    email_body = TEST_INDEED_ACCEPT_RESPONSE.format(guid)

    extracted_guid = find_guid(email_body)

    ###############################################################
    # with capsys.disabled():                                     #
    #     print("guid = \"{}\"".format(guid))                     #
    #     print("extracted_guid = \"{}\"".format(extracted_guid)) #
    ###############################################################

    assert guid == extracted_guid

def test_find_guid_anticase():
    global TEST_INDEED_ACCEPT_RESPONSE
    email_body = TEST_INDEED_ACCEPT_RESPONSE.format("this isn't a guid")
    extracted_guid = find_guid(email_body)
    assert not extracted_guid

@pytest.mark.django_db
def test_message_generation(capsys):
    jf = JobFamily()
    jf.save()
    j = Job(job_family=jf)
    j.save()
    u = User(name="The Dude")
    u.save()
    e = Employer(company_name="Foo, Inc.", short_company_name="Foo", company_description="Just another company")
    e.save()
    ej = EmployerJob(job_name="Philosopher", job_description="Make Kant look like a damn fool.", employer=e, job=j)
    ej.save()
    eu = EmployerUser(user=u, employer=e)
    eu.save()
    p = Profile(first_name="Big", last_name="Lebowski")
    p.save()
    ec = EmployerCandidate(profile_id=p.id, employer_user_id=eu.id, employer_job=ej)
    ec.save()
    pvr = ProfileVerificationRequest(metadata={'bkrnd_ecid': ec.id}, profile_id=p.id)

    with capsys.disabled():
        msg = get_message_for(pvr)

    assert msg.recruiter_name == u.name
    assert msg.company_name == e.company_name
    assert msg.job_title == ej.job_name
    assert ej.job_description in msg.job_description
    assert ec.guid is not None
    assert find_guid(msg.job_description) == str(ec.guid)

