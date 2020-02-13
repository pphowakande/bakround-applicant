
import pytest

from bakround_applicant.all_models.db import User, Profile, Job, JobFamily, \
                                             Employer, EmployerJob, EmployerCandidate, EmployerUser
from bakround_applicant.utilities.functions import has_candidate_accepted_request_for_job_associated_with_user
from bakround_applicant.utilities.helpers.dict import get_if_exists, get_first_matching
from bakround_applicant.utilities.helpers.datetime import parse_date_leniently, number_of_days_in_month


@pytest.mark.django_db
def test_has_candidate_accepted_request_for_job_associated_with_user():
    candidate_profile = Profile()
    candidate_profile.save()

    viewer_user = User.objects.create_user(username="first", password="first")
    viewer_user.save()

    assert not has_candidate_accepted_request_for_job_associated_with_user(candidate_profile.id, viewer_user.id)

    job_family = JobFamily()
    job_family.save()
    job = Job(job_family=job_family)
    job.save()
    employer = Employer(job_family=job_family)
    employer.save()
    employer_job = EmployerJob(employer=employer, job=job)
    employer_job.save()

    EmployerUser(employer=employer, user=viewer_user).save()

    employer_candidate = EmployerCandidate(profile=candidate_profile, employer_job=employer_job)
    employer_candidate.save()

    assert not has_candidate_accepted_request_for_job_associated_with_user(candidate_profile.id, viewer_user.id)

    employer_candidate.responded = True
    employer_candidate.accepted = True
    employer_candidate.save()
    assert has_candidate_accepted_request_for_job_associated_with_user(candidate_profile.id, viewer_user.id)


@pytest.mark.django_db
def test_get_if_exists():
    test_object = {"first": {"second": {"third": "goal"}}}
    assert get_if_exists(test_object, ["first", "second", "third"], "default") == "goal"
    assert get_if_exists(test_object, ["first", "second"], "default") == {"third": "goal"}
    assert get_if_exists(test_object, ["first", "second", "wrong"], "default") == "default"
    assert get_if_exists(test_object, [], "default") == "default"
    assert get_if_exists(test_object, ["first", "second", "third"], "default", return_as_list=True) == ["goal"]


@pytest.mark.django_db
def test_get_first_matching():
    states = [
        {"name": "Pennsylvania", "abbrev": "PA", "id": 50},
        {"name": "New Jersey", "abbrev": "NJ", "id": 49}
    ]
    assert get_first_matching(states, "abbrev", "PA", "name") == "Pennsylvania"
    assert get_first_matching(states, "abbrev", "<NJ>", "id", approximate_match=True) == 49
    assert get_first_matching(states, "abbrev", "DE", "name") is None


@pytest.mark.django_db
def test_parse_date_leniently():
    d = parse_date_leniently("2010-02-16")
    assert (d.year, d.month, d.day) == (2010, 2, 16)

    # June has 30 days
    d = parse_date_leniently("2012-06-31")
    assert (d.year, d.month, d.day) == (2012, 6, 30)

    # February 2016 had 29 days
    d = parse_date_leniently("2016-02-35")
    assert (d.year, d.month, d.day) == (2016, 2, 29)

    assert parse_date_leniently("nonsense!") is None

    with pytest.raises(ValueError):
        parse_date_leniently("2017-14-48")

    assert number_of_days_in_month(2017, 1) == 31
    assert number_of_days_in_month(2017, 2) == 28
    assert number_of_days_in_month(2016, 2) == 29
    assert number_of_days_in_month(2016, 4) == 30
