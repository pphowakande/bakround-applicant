
__author__ = "tplick"

import pytest
import json

from django.conf import settings
from bakround_applicant.all_models.db import Profile
from bakround_applicant.services.profiledeletionservice.consumer import Consumer


@pytest.mark.django_db
def test_profile_deletion():
    consumer = Consumer.__new__(Consumer)
    profile = Profile(id=9)
    profile.save()
    assert Profile.objects.count() == 1

    msg = {"profile_id": 9}
    consumer.handle_message(json.dumps(msg))
    assert Profile.objects.count() == 1

    profile.queued_for_deletion = True
    profile.save()
    consumer.handle_message(json.dumps(msg))
    assert Profile.objects.count() == 0
