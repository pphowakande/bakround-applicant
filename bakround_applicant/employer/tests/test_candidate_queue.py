
__author__ = "tplick"

import pytest
from bakround_applicant.all_models.db import Job, Employer, EmployerJob, \
            LookupState, Profile, EmployerCandidateQueue, EmployerSavedSearch, \
            User, EmployerUser, JobFamily, EmployerSearchResult, EmployerCandidate, \
            Score, EmployerJobUser
from bakround_applicant.employer.candidate_queue import add_candidates_to_queue, auto_contact_candidates, \
            remove_old_records_from_queue_for_employer_job
from test_employer_search import insert_real_distance_records, create_search_view, refresh_view

from django.utils import timezone


def set_up_test(is_bakround_employee):
    insert_real_distance_records()

    job_family = JobFamily()
    job_family.save()

    job = Job(job_family=job_family)
    job.save()

    employer = Employer(job_family=job_family)
    employer.save()

    employer_job = EmployerJob(job=job,
                               employer=employer,
                               city="Philadelphia",
                               state=LookupState.objects.get(state_code="PA"))
    employer_job.save()

    user = User.objects.create_user(username="a", email="b")
    user.save()

    employer_user = EmployerUser(user=user,
                                 employer=employer,
                                 is_bakround_employee=is_bakround_employee)
    employer_user.save()

    EmployerJobUser(employer_job=employer_job,
                    employer_user=employer_user).save()

    PA = LookupState.objects.get(state_code="PA")
    for i in range(5):
        profile = Profile(first_name=str(i),
                          last_name=str(i),
                          job=job,
                          city="Philadelphia",
                          state=PA)
        profile.save()

    search_parameters = {
        "page": 1,
        "certs": None,
        "score": None,
        "skills": None,
        "distance": 50,
        "ordering": "score",
        "languages": None,
        "page_size": 20,
        "experience": None,
        "state_filter": None,
        "min_education": None
    }

    saved_search = EmployerSavedSearch(employer_job=employer_job,
                                       employer_user=employer_user,
                                       search_parameters=search_parameters)
    saved_search.save()

    # Add two more profiles that appeared in a previous search.  These should not
    #   go into the queue.
    for i in [10, 11]:
        profile = Profile(first_name=str(i),
                          last_name=str(i),
                          job=job,
                          city="Philadelphia",
                          state=PA)
        profile.save()

        EmployerSearchResult(profile=profile,
                             employer_user=employer_user,
                             employer_saved_search=saved_search,
                             opened=True).save()


def _test_candidate_queue(is_bakround_employee):
    set_up_test(is_bakround_employee)
    create_search_view()

    assert EmployerCandidateQueue.objects.count() == 0

    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 0

    employer = Employer.objects.first()
    employer.candidate_queue_enabled = True
    employer.save()

    add_candidates_to_queue()
    # the profiles have no scores yet
    assert EmployerCandidateQueue.objects.count() == 0

    add_score_for_every_profile(350)
    # the profiles are scored too low
    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 0

    add_score_for_every_profile(700)
    # the profiles are scored high enough now
    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 0  # the job does not have the queue or auto-contact enabled

    EmployerJob.objects.update(candidate_queue_enabled=True,
                               auto_contact_enabled=True)
    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 5

    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 5

    profile = Profile.objects.order_by('id').first()
    profile.last_updated_date = timezone.now()
    profile.save()

    refresh_view()
    add_candidates_to_queue()
    assert EmployerCandidateQueue.objects.count() == 5
    # print(EmployerCandidateQueue.objects.values_list("profile_id", "profile__first_name"))
    assert EmployerCandidateQueue.objects.values("profile_id").distinct().count() == 5


    # now test the auto-contact feature

    assert EmployerCandidate.objects.count() == 0

    employer = Employer.objects.first()
    employer.auto_contact_enabled = True
    employer.save()

    # add a recently contacted candidate for one of the queued profiles
    employer_job = EmployerJob.objects.first()
    EmployerCandidate(profile=profile,
                      employer_job=employer_job,
                      contacted=True,
                      contacted_date=timezone.now()).save()

    assert EmployerCandidate.objects.count() == 1

    auto_contact_candidates(send_email=False)
    assert EmployerCandidate.objects.count() == 1  # because the user does not have auto-contact enabled

    employer_user = EmployerUser.objects.get()
    employer_user.auto_contact_enabled = True
    employer_user.save()
    auto_contact_candidates(send_email=False)
    assert EmployerCandidate.objects.count() == 5


    # test deletion

    new_profiles = []
    job = Job.objects.first()
    saved_search = EmployerSavedSearch.objects.first()

    for _ in range(2000):
        profile = Profile(job=job)
        profile.save()

        record = EmployerCandidateQueue(employer_job=employer_job,
                                        profile=profile,
                                        employer_saved_search=saved_search,
                                        employer_user=employer_user)
        record.save()

        new_profiles.append(profile)

    assert EmployerCandidateQueue.objects.count() == 2005

    remove_old_records_from_queue_for_employer_job(employer_job)
    assert EmployerCandidateQueue.objects.count() == 2000

    for _ in range(80):
        auto_contact_candidates(send_email=False)  # 25 at a time

    remove_old_records_from_queue_for_employer_job(employer_job)
    assert EmployerCandidateQueue.objects.count() == 1900


def add_score_for_every_profile(score_value):
    for profile in Profile.objects.all():
        score = Score(profile=profile,
                      job=profile.job,
                      score_value=score_value)
        score.save()

    refresh_view()



@pytest.mark.django_db
def test_candidate_queue_with_non_bakround_employee():
    _test_candidate_queue(False)


@pytest.mark.django_db
def test_candidate_queue_with_bakround_employee():
    _test_candidate_queue(True)
