
__author__ = "tplick"

import pytest
from bakround_applicant.profile.metric import calculate_completeness_metric_and_hints
from bakround_applicant.all_models.db import Profile, Skill, Certification, \
                        ProfileSkill, ProfileEducation, ProfileExperience, \
                        LookupDegreeMajor, LookupDegreeName, LookupDegreeType, ProfileCertification, \
                        LookupState
import datetime
from django.utils import timezone


@pytest.mark.django_db
def test_metric_for_empty_profile():
    profile = Profile()
    profile.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 0
    assert set(metric['hints']['add'].keys()) == {'skill', 'education', 'experience'}


@pytest.mark.django_db
def test_metric_for_profile_with_one_skill():
    profile = Profile()
    profile.save()

    skill = Skill(skill_name='whatever')
    skill.save()

    profile_skill = ProfileSkill(profile=profile, skill=skill, skill_name=skill.skill_name)
    profile_skill.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 30
    assert set(metric['hints']['add'].keys()) == {'education', 'experience'}
    assert set(metric['hints']['detail'].keys()) == {'skill'}
    assert set(metric['hints']['error'].keys()) == set()

    profile_skill.experience_months = 5
    profile_skill.last_used_date = timezone.now()

    profile_skill.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 33
    assert set(metric['hints']['add'].keys()) == {'education', 'experience'}
    assert set(metric['hints']['detail'].keys()) == set()
    assert set(metric['hints']['error'].keys()) == set()


@pytest.mark.django_db
def test_required_field_message():
    now = timezone.now()

    state = LookupState(state_code='PA', state_name='Pennsylvania')
    state.save()

    profile = Profile()
    profile.save()

    experience = ProfileExperience(profile=profile)
    experience.company_name = None
    experience.position_title = None
    experience.position_description = None
    experience.start_date = experience.end_date = now
    experience.city = 'Philadelphia'
    experience.state = state
    experience.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 20
    assert set(metric['hints']['add']) == {'skill', 'education'}
    assert set(metric['hints']['detail']) == {'experience'}
    assert set(metric['hints']['error']) == {'experience'}

    experience.position_description = "This is a description."
    experience.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 23
    assert set(metric['hints']['add']) == {'skill', 'education'}
    assert set(metric['hints']['detail']) == set()
    assert set(metric['hints']['error']) == {'experience'}

    experience.company_name = 'Company A'
    experience.position_title = 'RN'
    experience.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 33
    assert set(metric['hints']['add']) == {'skill', 'education'}
    assert set(metric['hints']['detail']) == set()
    assert set(metric['hints']['error']) == set()


@pytest.mark.django_db
def test_metric_for_profile_with_certification_error():
    now = timezone.now()

    profile = Profile()
    profile.save()

    skill = Skill(skill_name='whatever')
    skill.save()

    profile_skill = ProfileSkill(profile=profile,
                                 skill=skill,
                                 skill_name=skill.skill_name,
                                 experience_months=6,
                                 last_used_date=now)
    profile_skill.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 33
    assert set(metric['hints']['add'].keys()) == {'education', 'experience'}
    assert set(metric['hints']['detail'].keys()) == set()
    assert set(metric['hints']['error'].keys()) == set()

    cert = Certification(certification_name="Registered Nurse")
    cert.save()

    profile_certification = ProfileCertification(profile=profile,
                                                 certification=cert,
                                                 certification_name=cert.certification_name,
                                                 issued_date=None)
    profile_certification.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 23
    assert set(metric['hints']['add'].keys()) == {'education', 'experience'}
    assert set(metric['hints']['detail'].keys()) == set()
    assert set(metric['hints']['error'].keys()) == {'certification'}

    profile_certification.certification_name = 'Test Cert'
    profile_certification.issued_date = now
    profile_certification.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 33
    assert set(metric['hints']['add'].keys()) == {'education', 'experience'}
    assert set(metric['hints']['detail'].keys()) == set()
    assert set(metric['hints']['error'].keys()) == set()


@pytest.mark.django_db
def test_metric_for_complete_profile():
    now = timezone.now()

    state = LookupState(state_code='PA', state_name='Pennsylvania')
    state.save()

    profile = Profile()
    profile.save()

    skill = Skill(skill_name='underwater basket weaving')
    skill.save()

    ProfileSkill(profile=profile,
                 skill=skill,
                 skill_name=skill.skill_name,
                 experience_months=6,
                 last_used_date=now).save()

    education = ProfileEducation(profile=profile)
    education.school_name = 'Collegiate University'
    education.degree_date = now
    education.degree_major = make_new_row(LookupDegreeMajor)
    education.degree_name = make_new_row(LookupDegreeName)
    education.degree_type = make_new_row(LookupDegreeType)
    education.save()

    experience = ProfileExperience(profile=profile)
    experience.company_name = 'Bakround'
    experience.position_title = 'Automated Tester'
    experience.position_description = 'I test things'
    experience.start_date = experience.end_date = now
    experience.city = 'City'
    experience.state = state
    experience.save()

    metric = calculate_completeness_metric_and_hints(profile)
    assert metric['metric'] == 100
    assert set(metric['hints']['add'].keys()) == set()
    assert set(metric['hints']['detail'].keys()) == set()
    assert set(metric['hints']['error'].keys()) == set()


def make_new_row(model):
    row = model()
    row.save()
    return row
