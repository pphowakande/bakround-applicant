

import pytest
from decimal import Decimal

from django.core.cache import cache
from django.test.client import Client
from django_redis import get_redis_connection
from django.shortcuts import reverse

from bakround_applicant.all_models.db import User, SME, Job, SMEPayRate, JobFamily


@pytest.mark.django_db
def test_create_and_remove_sme():
    user = User.objects.create_user(username="first", password="first")
    client = Client()
    client.force_login(user)

    assert SME.objects.count() == 0

    family = JobFamily(family_name="nursing")
    family.save()
    job = Job(job_name="Nurse", id=1, job_family=family)
    job.save()

    sme_data = {"first_name": "Bob",
                "last_name": "Loblaw",
                "email": "bob@loblaw.com",
                "review_limit": "10",
                "job": "1",
                "pay_rate": "0.05"}

    # first try to add without having staff privilege
    client.post(reverse("sme_manager:create_sme"), sme_data)
    assert SME.objects.count() == 0
    assert SME.objects.filter(active=True).count() == 0

    user.is_staff = True
    user.save()
    client.post(reverse("sme_manager:create_sme"), sme_data)
    assert SME.objects.count() == 1
    assert SME.objects.filter(active=True).count() == 1

    sme = SME.objects.first()
    assert sme.first_name == "Bob"
    assert sme.last_name == "Loblaw"
    assert sme.job_id == 1

    assert SMEPayRate.objects.count() == 1
    pay_rate = SMEPayRate.objects.get(sme=sme)
    assert pay_rate.pay_rate == Decimal("0.05")

    sme_data = {"sme_id": SME.objects.first().id}
    client.post(reverse("sme_manager:delete_sme", kwargs=sme_data))
    assert SME.objects.count() == 1
    assert SME.objects.filter(active=True).count() == 0


"""
@pytest.mark.django_db
def test_clear_cache():
    user = User.objects.create_user(username="first", password="first")
    client = Client()
    client.force_login(user)

    redis = get_redis_connection("default")
    print(dir(redis))

    cache.set("key", "value", 3600)
    assert cache.get("key") == "value"

    client.get("/admin/clear_cache/")
    assert cache.get("key") == "value"

    user.is_superuser = True
    user.save()
    client.get("/admin/clear_cache/")
    assert cache.get("key") is None
"""
