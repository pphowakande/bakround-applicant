
__author__ = "tplick"

import pytest
from bakround_applicant.employer.tests import test_candidate_queue
from bakround_applicant.all_models.db import EmployerUser, EmployerJob, EmployerJobUser, \
                                             Profile, EmployerCandidate, ProfileEmail, \
                                             NotificationRecipientEvent
from bakround_applicant.employer.utils import full_name_of_employer_user, get_recruiter_for_job, \
                                              get_email_address_for_responding_candidate
from bakround_applicant.services.verifyingservice.util import add_contact, collect_contact_info_for_profile, collect_email_data

def _test_auto_respond_functions(is_bakround_employee):
    test_candidate_queue.set_up_test(is_bakround_employee)

    employer_user = EmployerUser.objects.first()
    employer_job = EmployerJob.objects.first()

    user = employer_user.user
    user.first_name, user.last_name = "Bob", "Loblaw"
    user.save()

    assert full_name_of_employer_user(employer_user) == "Bob Loblaw"

    assert get_recruiter_for_job(employer_job) == employer_user

    profile = Profile.objects.first()
    collect_contact_info_for_profile(profile)
    candidate = EmployerCandidate(profile=profile,
                                  employer_job=employer_job,
                                  employer_user=employer_user)
    candidate.save()

    # First, test the case where old data is used.

    cd = ProfileEmail(profile=profile, value="c@d.com")
    cd.save()
    assert get_email_address_for_responding_candidate(candidate) is None

    NotificationRecipientEvent(action="open", email=cd.value).save()
    collect_email_data(cd)
    assert get_email_address_for_responding_candidate(candidate) == cd.value

    NotificationRecipientEvent(action="unsubscribe", email=cd.value).save()
    collect_email_data(cd)
    assert get_email_address_for_responding_candidate(candidate) is None

    # Then, test the case where new data is used.

    e = ProfileEmail(profile=profile, value="e@f.com")
    e.save()
    assert get_email_address_for_responding_candidate(candidate) is None

    e.opens = True
    e.save()
    assert get_email_address_for_responding_candidate(candidate) == e.value

    e.unsubscribed = True
    e.save()
    assert get_email_address_for_responding_candidate(candidate) is None

@pytest.mark.django_db
def test_auto_respond_with_non_bakround_employee():
    _test_auto_respond_functions(False)


@pytest.mark.django_db
def test_auto_respond_with_bakround_employee():
    _test_auto_respond_functions(True)
