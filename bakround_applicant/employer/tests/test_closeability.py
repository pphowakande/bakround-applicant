
__author__ = "tplick"

import pytest
from datetime import datetime, timedelta
from django.utils import timezone

from bakround_applicant.all_models.db import Profile, ProfileExperience, Job, EmployerJob, \
                                             Employer, LookupState, JobFamily
from bakround_applicant.employer.closeability_metric import \
    fetch_closeability_metric_for_profile_ids, time_in_current_job, \
    average_time_in_each_job, attach_experience_to_profiles
from test_employer_search import insert_real_distance_records

from django.core.cache import cache


@pytest.mark.django_db
def test_closeability():
    insert_real_distance_records()
    PA = LookupState.objects.get(state_code="PA")

    profile = Profile(id=19)
    profile.save()
    attach_experience_to_profiles({profile.id: profile})
    assert average_time_in_each_job(profile) == timedelta(days=0)

    job_family = JobFamily(id=1)
    job_family.save()
    job = Job(job_family=job_family)
    job.save()
    employer = Employer(id=1)
    employer.save()
    employer_job = EmployerJob(id=1,
                               employer_id=1,
                               job=job,
                               city="Philadelphia",
                               state=PA)
    employer_job.save()

    cache.clear()
    clos = fetch_closeability_metric_for_profile_ids([19], 1)
    assert list(clos.keys()) == [19]
    assert isinstance(clos[19], float)
    assert clos[19] == -1.0

    profile.city = "Philadelphia"
    profile.state = PA
    profile.save()
    cache.clear()
    assert fetch_closeability_metric_for_profile_ids([19], 1)[19] == 0.0

    assert time_in_current_job(profile).days == 0

    now = timezone.now()
    ProfileExperience(profile=profile,
                      start_date=now-timedelta(days=365*10),
                      end_date=now-timedelta(days=365),
                      is_current_position=False).save()
    ProfileExperience(profile=profile,
                      start_date=now-timedelta(days=180),
                      city="Philadelphia",
                      state=PA,
                      is_current_position=True).save()
    attach_experience_to_profiles({profile.id: profile})

    assert time_in_current_job(profile).days == 180

    # the profile's total work time is a little less than 9.5 years
    average_time = average_time_in_each_job(profile)
    assert 365*4.5 < average_time.days < 365*5

    cache.clear()
    new_metric = fetch_closeability_metric_for_profile_ids([19], 1)[19]
    assert abs(new_metric - 0.5) < 0.1

    # ==================================================================

    # to test batching, we'll calculate the metric for 1000 profiles now

    profile_ids = list(range(1000, 2000))

    for pid in profile_ids:
        Profile(id=pid,
                city="Philadelphia",
                state=PA).save()

        ProfileExperience(profile=profile,
                          start_date=now-timedelta(days=365),
                          end_date=now-timedelta(days=30),
                          is_current_position=False).save()

    cache.clear()
    metrics = fetch_closeability_metric_for_profile_ids(profile_ids, 1)

    # make sure we have a result for every profile
    assert sorted(metrics.keys()) == profile_ids
