
__author__ = "tplick"

from django.core.urlresolvers import reverse, resolve
from django.test import Client
import pytest
from bakround_applicant.all_models.db import User, Profile, Job, LookupState, ProfileExperience, \
                                             Employer, EmployerUser, SME, ProfileResume, \
                                             EmployerCandidate, JobFamily
import random
import string

from datetime import datetime, timedelta
from django.utils import timezone


# I couldn't find a good way of fetching all the pages from
#   the url conf, so I am going to create a list here and
#   update it periodically.

PAGES_FOR_NORMAL_USERS = [
    '/profile/',
    '/settings/',
    '/users/change_job/',
    '/profile/share_profile',
    '/legal/',
]

PAGES_FOR_STAFF = [
    '/job_manager/',
    '/job_manager/?job_id=1',
    '/sme_manager/',
    '/skill_manager/',
]

PAGES_FOR_EMPLOYERS = [
    '/employer/jobs',
]

PAGES_FOR_ICIMS = [
    '/icims/jobs',
    '/icims/search',
    'icims/stats'
]

PAGES_FOR_NON_REGISTERED_USERS =[
    '/accounts/signup/',
    '/accounts/login/',
    '/legal/',
]


@pytest.mark.django_db
def test_pages_accessible_to_normal_users():
    client = make_logged_in_client(is_staff=False)
    make_test_profile()

    for page in PAGES_FOR_NORMAL_USERS:
        assert client.get(page).status_code == 200

    for page in PAGES_FOR_STAFF:
        assert client.get(page).status_code == 302

    for page in PAGES_FOR_EMPLOYERS:
        assert client.get(page).status_code == 302


@pytest.mark.django_db
def test_pages_accessible_to_staff_users():
    client = make_logged_in_client(is_staff=True)
    make_test_profile()

    for page in PAGES_FOR_NORMAL_USERS:
        assert client.get(page).status_code == 200

    for page in PAGES_FOR_STAFF:
        assert client.get(page).status_code == 200

    for page in PAGES_FOR_EMPLOYERS:
        assert client.get(page).status_code == 302


@pytest.mark.django_db
def test_pages_accessible_to_employer_users():
    client = make_logged_in_client(is_employer=True)
    make_test_profile()

    assert EmployerCandidate.objects.count() == 0

    for page in PAGES_FOR_NORMAL_USERS:
        assert client.get(page).status_code == 200

    for page in PAGES_FOR_STAFF:
        assert client.get(page).status_code == 302

    for page in PAGES_FOR_EMPLOYERS:
        assert client.get(page).status_code == 200


def make_logged_in_client(is_staff=False, is_employer=False):
    client = Client()

    # create a staff user and log them in
    new_username = ''.join(random.choice(string.ascii_letters) for i in range(30))
    user = User.objects.create_user(username=new_username, email=new_username)
    user.is_staff = is_staff
    user.save()
    client.force_login(user)

    # create a profile for this user
    Job(id=1, job_name="fake").save()
    Profile(user=user, job_id=1).save()

    if is_employer:
        user.is_employer = True
        user.save()

        job_family = JobFamily()
        job_family.save()
        employer = Employer(company_name="Excellence Incorporated",
                            job_family=job_family)
        employer.save()
        EmployerUser(employer=employer,
                     user=user,
                     is_billing_admin=True).save()

    return client


@pytest.mark.django_db
def test_pages_accessible_to_non_registered_users():
    client = Client()
    make_test_profile()

    for page in PAGES_FOR_NON_REGISTERED_USERS:
        assert client.get(page).status_code == 200

    for page in PAGES_FOR_STAFF:
        assert client.get(page).status_code == 302

    for page in PAGES_FOR_EMPLOYERS:
        assert client.get(page).status_code == 302


def contents_of_page(page):
    return page.content.decode('utf8')


@pytest.mark.django_db
def test_loading_sme_feedback_page():
    job = Job()
    job.save()
    sme = SME(guid="first", job=job)
    sme.save()
    client = Client()
    url = "/sme_feedback/"

    # load SME page with no token
    page = client.get(url)
    assert "error:" in contents_of_page(page).lower()

    # load SME page with bad token
    page = client.get(url + "?token=bad")
    assert "error:" in contents_of_page(page).lower()

    # load SME page with correct token
    page = client.get(url + "?token=first")
    assert "error:" not in contents_of_page(page).lower()

    # there are no resumes yet, so the page should say "try again later"
    assert "try again later" in contents_of_page(page).lower()

    # let's add a resume and check that that message is gone
    profile = Profile(job=job)
    profile.save()
    ProfileResume(profile=profile).save()
    page = client.get(url + "?token=first")
    assert "try again later" not in contents_of_page(page).lower()
    assert "see description" in contents_of_page(page).lower()


def make_test_profile():
    state = LookupState(state_code='PA', state_name='Pennsylvania')
    state.save()

    profile = Profile(id=1)
    profile.save()

    for duration in (60, 180, 400, 700, 2000, 7000):
        experience = ProfileExperience(profile=profile)
        experience.company_name = None
        experience.position_title = None
        experience.position_description = None
        experience.end_date = timezone.now()
        experience.start_date = timezone.now() - timedelta(days=duration)
        experience.city = 'Philadelphia'
        experience.state = state
        experience.save()
