
__author__ = "tplick"

import pytest
from django.test import Client
from django.shortcuts import reverse
from bakround_applicant.all_models.db import User, Profile, Job


@pytest.mark.django_db
def test_add_and_delete_job():
    user = User.objects.create_user(username="a", password="b")
    user.is_staff = True
    user.save()

    client = Client()
    client.force_login(user)

    assert Job.objects.count() == 0
    params = {
        "name_for_new_job": "Zamboni operator",
        "description_for_new_job": "operate the Zamboni",
        "job_family": 1,
        "onet_position": 0,
        "accuracy": "2",
    }
    client.post(reverse("job_manager:add_job"), params)
    assert Job.objects.count() == 1

    job = Job.objects.first()
    assert job.job_name == "Zamboni operator"
    assert job.job_description == "operate the Zamboni"

    client.post(reverse("job_manager:delete_job"), {"job_id": job.id})
    assert Job.objects.count() == 0

    user.is_staff = False
    user.save()
    client.post(reverse("job_manager:add_job"), params)
    assert Job.objects.count() == 0

    client.logout()
