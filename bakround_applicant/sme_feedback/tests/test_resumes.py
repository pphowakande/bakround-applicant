# tplick, 29 December 2016

import random
import string
import pytest

from collections import defaultdict

from bakround_applicant.all_models.db import User, Profile, Job, ProfileResume, SME, SMEFeedback, \
                                             LookupPhysicalLocation, LookupState, LookupRegion

from bakround_applicant.sme_feedback.views import has_sme_reached_their_review_limit
from bakround_applicant.sme_feedback.util import rereview_probability_for_job, \
                                            choose_random_unreviewed_resume_for_sme, \
                                            filter_resumes_by_region


def create_random_user():
    name = ''.join(random.choice(string.ascii_letters) for i in range(20))
    user_obj = User(username=name, email=name + "-testing@bakround.com")
    user_obj.save()
    return user_obj

def create_dummy_job(job_id):
    Job(id=job_id).save()

def create_dummy_profile(profile_id, job_id):
    Profile(id=profile_id, job_id=job_id).save()

def create_dummy_resume(id, profile_id):
    ProfileResume(id=id, profile_id=profile_id).save()

extra_info = {"job_id": 1}

@pytest.mark.django_db
def test_sme_resume_chooser():
    create_dummy_job(job_id=1)

    # create new SME
    sme = SME(guid='whatever', job_id=1)
    sme.save()

    # fetch resume to show this SME
    resume = choose_random_unreviewed_resume_for_sme(sme)

    # since we did not create any resumes in the mock database,
    #       resume should be None
    assert resume is None

    # now, create a profile for a job that is not the SME's job
    create_dummy_job(job_id=2)
    create_dummy_profile(1, job_id=2)
    create_dummy_resume(1, profile_id=1)

    # there is still no resume for the SME
    resume = choose_random_unreviewed_resume_for_sme(sme)
    assert resume is None

    # now, create a profile for the sme's job
    create_dummy_profile(2, job_id=1)
    create_dummy_resume(2, profile_id=2)

    # try again to fetch a resume
    resume = choose_random_unreviewed_resume_for_sme(sme)

    # this time, we should have a non-null value, since there is a profile that
    #      matches the SME's job_id
    assert resume is not None
    assert resume.id == 2
    assert resume.profile_id == 2


@pytest.mark.django_db
def test_sme_is_not_shown_same_resume_twice():
    create_dummy_job(1)
    sme = SME(guid='whatever', job_id=1)
    sme.save()

    create_dummy_profile(1, job_id=1)
    create_dummy_profile(2, job_id=1)

    create_dummy_resume(5, profile_id=1)
    create_dummy_resume(6, profile_id=2)

    # ensure that the random choice eventually gives us all the resumes
    ids_seen = set()
    for i in range(100):
        resume = choose_random_unreviewed_resume_for_sme(sme)
        assert resume is not None
        ids_seen.add(resume.id)
    assert ids_seen == {5, 6}

    # simulate the SME reviewing resume #5
    SMEFeedback(sme=sme,
                profile_resume_id=5,
                should_interview=True).save()

    for i in range(100):
        resume = choose_random_unreviewed_resume_for_sme(sme)
        assert resume is not None
        assert resume.id == 5 or resume.id == 6


@pytest.mark.django_db
def test_resume_choices_with_two_smes():
    create_dummy_job(1)
    sme1 = SME(guid="first", job_id=1)
    sme1.save()

    sme2 = SME(guid="second", job_id=1)
    sme2.save()

    create_dummy_profile(1, job_id=1)
    create_dummy_profile(2, job_id=1)

    create_dummy_resume(7, profile_id=1)
    create_dummy_resume(9, profile_id=2)

    assert all_resumes_to_show_to_sme(sme1) == {7, 9}
    assert all_resumes_to_show_to_sme(sme2) == {7, 9}

    # now let's suppose sme1 reviews resume #9
    SMEFeedback(sme=sme1,
                profile_resume_id=9,
                should_interview=False).save()

    assert all_resumes_to_show_to_sme(sme1) == {7}
    assert all_resumes_to_show_to_sme(sme2) == {7, 9}

    # Now let's suppose that sme2 marks resume #7 as wrong_job...
    # neither sme should see resume #7 from now on.
    SMEFeedback(sme=sme2,
                profile_resume_id=7,
                should_interview=False,
                wrong_job=True).save()
    assert all_resumes_to_show_to_sme(sme1) == set()
    assert all_resumes_to_show_to_sme(sme2) == {9}

    # Now suppose that resume #9 is marked as wrong_language.
    SMEFeedback(sme=sme2,
                profile_resume_id=9,
                should_interview=False,
                wrong_language=True).save()

    # At this point, both resumes were disqualified.
    # A new SME should not see any resumes, nor should any of the others.
    sme3 = SME(guid="third", job_id=1)
    sme3.save()
    assert all_resumes_to_show_to_sme(sme1) == set()
    assert all_resumes_to_show_to_sme(sme2) == set()
    assert all_resumes_to_show_to_sme(sme3) == set()


def all_resumes_to_show_to_sme(sme):
    ids_seen = set()

    # Try at most 100 times.
    for iteration in range(100):
        resume = choose_random_unreviewed_resume_for_sme(sme, 0.5)
        if resume:
            ids_seen.add(resume.id)

    return ids_seen


@pytest.mark.django_db
def test_sme_review_limit():
    create_dummy_job(1)
    limited_sme = SME(guid="first", job_id=1, review_limit=5)
    unlimited_sme = SME(guid="second", job_id=1, review_limit=None)
    limited_sme.save()
    unlimited_sme.save()

    for i in range(5):
        assert has_sme_reached_their_review_limit(limited_sme) is False
        assert has_sme_reached_their_review_limit(unlimited_sme) is False

        # Add a new resume, and pretend that each SME reviews it.

        new_profile_id = new_resume_id = i + 1
        create_dummy_profile(new_profile_id, job_id=1)
        create_dummy_resume(new_resume_id, profile_id=new_profile_id)

        for sme in (limited_sme, unlimited_sme):
            SMEFeedback(sme=sme,
                        profile_resume_id=new_resume_id,
                        should_interview=False).save()

    # At this point, each SME has reviewed 5 resumes.
    assert has_sme_reached_their_review_limit(limited_sme) is True
    assert has_sme_reached_their_review_limit(unlimited_sme) is False


@pytest.mark.django_db
def test_choosing_resume_with_bias_toward_already_reviewed():
    create_dummy_job(1)
    sme1 = SME(guid="first", job_id=1)
    sme1.save()
    sme2 = SME(guid="second", job_id=1)
    sme2.save()

    create_dummy_profile(1, job_id=1)
    create_dummy_profile(2, job_id=1)
    create_dummy_resume(6, profile_id=1)
    create_dummy_resume(8, profile_id=2)

    # Pretend that sme1 reviews resume #8.
    SMEFeedback(sme=sme1, profile_resume_id=8, should_interview=False).save()

    assert all_resumes_to_show_to_sme(sme1) == {6}
    assert all_resumes_to_show_to_sme(sme2) == {6, 8}

    # Let us now choose a resume for SME2, but with the probability of choosing
    #     an already-reviewed resume set to 1.  Each choice should give us
    #     resume #8, since that is the only resume that has a review.
    for i in range(20):
        choice = choose_random_unreviewed_resume_for_sme(sme2, 1.0)
        assert choice and choice.id == 8


@pytest.mark.django_db
def test_choose_random_element_from_queryset():
    # Make sure that the choice is fairly random.  To make this pretty simple,
    #    we'll just say that we should have at least one element from 1..10 and
    #    at least one element from 11..20.
    # We need to choose *something*, so we'll populate the job table and pick
    #    from there.

    for i in range(20):
        create_dummy_job(i+1)

    queryset = Job.objects.all().order_by('id')
    choices = set()

    for i in range(20):
        choice = queryset.order_by('?').first()
        assert choice is not None
        choices.add(choice.id)

    one_to_ten = set(range(1, 11))
    eleven_to_twenty = set(range(11, 21))

    assert len(choices & one_to_ten) > 0
    assert len(choices & eleven_to_twenty) > 0


@pytest.mark.django_db
def test_rereview_probability_for_job():
    desired_probabilities = {
        1:   1.0,
        5:   0.95,
        8:   0.4,
        20:  0.4,
    }
    default_probability = 0.05

    for job_id in (1, 5, 8, 20, 1000):
        job = Job(id=job_id)
        job.save()
        assert rereview_probability_for_job(job) == desired_probabilities.get(job_id, default_probability)


@pytest.mark.django_db
def test_rereview_probability_for_job():
    job = Job(id=1)
    job.save()
    assert rereview_probability_for_job(job) == 0.01

    guids = list(str(n) for n in range(5000))

    for _ in range(600):
        resume = create_resume_for_job(job)
        resume.save()

        sme = SME(job=job,
                  guid=guids.pop(0))
        sme.save()

        SMEFeedback(sme=sme,
                    profile_resume=resume,
                    should_interview=False).save()

    assert rereview_probability_for_job(job) == 0.60

    # review each resume three more times

    for resume in ProfileResume.objects.all():
        for _ in range(3):
            sme = SME(job=job,
                      guid=guids.pop(0))
            sme.save()

            SMEFeedback(sme=sme,
                        profile_resume=resume,
                        should_interview=False).save()

    assert rereview_probability_for_job(job) == 0.01

    # bring number of reviewed resumes up to 1400

    for _ in range(800):
        resume = create_resume_for_job(job)
        resume.save()

        sme = SME(job=job,
                  guid=guids.pop(0))
        sme.save()

        SMEFeedback(sme=sme,
                    profile_resume=resume,
                    should_interview=False).save()

    assert rereview_probability_for_job(job) == 0.5


def create_resume_for_job(job):
    profile = Profile(job=job)
    profile.save()

    resume = ProfileResume(profile=profile)
    return resume


@pytest.mark.django_db
def test_limits_on_reviews_per_resume_per_sme():
    job = Job(id=1)
    job.save()
    sme = SME(job=job)
    sme.save()
    profile = Profile(job=job)
    profile.save()
    resume = ProfileResume(profile=profile)
    resume.save()

    assert choose_random_unreviewed_resume_for_sme(sme).id == resume.id

    SMEFeedback(sme=sme,
                profile_resume=resume,
                should_interview=True).save()


    SMEFeedback(sme=sme,
                profile_resume=resume,
                should_interview=True).save()

    SMEFeedback(sme=sme,
                profile_resume=resume,
                should_interview=True).save()

    new_resume = ProfileResume(profile=profile)
    new_resume.save()

    SMEFeedback(sme=sme,
                profile_resume=new_resume,
                should_interview=False).save()

    SMEFeedback(sme=sme,
                profile_resume=new_resume,
                should_interview=False).save()

    assert choose_random_unreviewed_resume_for_sme(sme) is None

@pytest.mark.django_db
def test_resume_regions():
    add_cities()

    PA, NJ, CA = [LookupState.objects.get(state_code=state_code)
                  for state_code in ["PA", "NJ", "CA"]]

    pa_region = LookupRegion(city="Philadelphia",
                             state=PA)
    pa_region.save()
    ca_region = LookupRegion(city="San Francisco",
                             state=CA)
    ca_region.save()

    job = Job()
    job.save()

    create_resumes_for_location(job, 3, "Philadelphia", PA)
    create_resumes_for_location(job, 5, "Haddonfield", NJ)
    create_resumes_for_location(job, 6, "San Francisco", CA)

    all_resumes = ProfileResume.objects.filter(profile__job=job)

    assert filter_resumes_by_region(all_resumes, None).count() == 14
    assert filter_resumes_by_region(all_resumes, pa_region).count() == 8
    assert filter_resumes_by_region(all_resumes, ca_region).count() == 6

    pa_sme = SME(job=job,
                 region=pa_region,
                 guid="pa")
    pa_sme.save()
    ca_sme = SME(job=job,
                 region=ca_region,
                 guid="ca")
    ca_sme.save()

    for _ in range(20):
        resume = choose_random_unreviewed_resume_for_sme(pa_sme)
        assert resume.profile.state.state_code in ("PA", "NJ")

        resume = choose_random_unreviewed_resume_for_sme(ca_sme)
        assert resume.profile.state.state_code == "CA"

    # test region radius
    assert filter_resumes_by_region(all_resumes, pa_region).count() == 8
    pa_region.radius = 100
    pa_region.save()
    assert filter_resumes_by_region(all_resumes, pa_region).count() == 8
    pa_region.radius = 5
    pa_region.save()
    assert filter_resumes_by_region(all_resumes, pa_region).count() == 3


def add_cities():
    records = [("Philadelphia", "PA", 39.9522222, -75.1641667),
               ("Haddonfield", "NJ", 39.8913889, -75.0380556),
               ("San Francisco", "CA", 37.775, -122.4183333)]

    for (city, state_code, latitude, longitude) in records:
        state = LookupState(state_code=state_code)
        state.save()

        location = LookupPhysicalLocation(city=city,
                                          state=state,
                                          latitude=latitude,
                                          longitude=longitude)
        location.save()


def create_resumes_for_location(job, count, city, state):
    for _ in range(count):
        profile = Profile(job=job,
                          city=city,
                          state=state)
        profile.save()

        resume = ProfileResume(profile=profile)
        resume.save()
