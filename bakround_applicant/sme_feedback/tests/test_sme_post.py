
__author__ = "tplick"

import pytest
from django.test import Client
from django.shortcuts import reverse

from bakround_applicant.all_models.db import Job, Profile, ProfileResume, \
                                             SMEFeedback, SME


@pytest.mark.django_db
def test_sme_post():
    job = Job(id=1)
    job.save()

    sme = SME(id=4, guid="four", job=job)
    sme.save()

    Profile(id=2, job_id=1).save()
    ProfileResume(id=4, profile_id=2).save()

    url = reverse("resumes:sme_feedback")
    client = Client()

    params = {
        "token": "four",
        "comment": "comment",
        "should_interview": "1",
        "resume_id": 4,
        "feedback_guid": "1234",
        "bscore_value": "501",
    }

    assert SMEFeedback.objects.count() == 0
    client.post(url, params)
    assert SMEFeedback.objects.count() == 1
    client.post(url, params)
    assert SMEFeedback.objects.count() == 1

    feedback = SMEFeedback.objects.first()
    assert feedback.bscore_value == 501
    assert feedback.comment == "comment"
    assert feedback.wrong_language is False

    params['feedback_guid'] = "5678"
    params['column_wrong_language'] = True
    client.post(url, params)
    assert SMEFeedback.objects.count() == 2
    assert SMEFeedback.objects.filter(wrong_language=True).count() == 1

    params['feedback_guid'] = "9abc"
    params['token'] = "wrong"
    with pytest.raises(Exception):
        client.post(url, params)
    assert SMEFeedback.objects.count() == 2
