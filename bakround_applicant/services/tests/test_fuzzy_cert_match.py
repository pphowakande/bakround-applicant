
__author__ = "tplick"

import pytest
from bakround_applicant.all_models.db import Certification
from bakround_applicant.services.buildprofile.service import get_best_matching_certification_id
from django.db import connection


@pytest.mark.django_db
def test_fuzzy_cert_match():
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")

    Certification(id=1, certification_name="Nurse").save()
    Certification(id=2, certification_name="z"*400).save()

    assert get_best_matching_certification_id("Nurse") == 1
    assert get_best_matching_certification_id("Nursing") == 1
    assert get_best_matching_certification_id("1234567") is None
    assert get_best_matching_certification_id("z"*400) == 2
    assert get_best_matching_certification_id("z"*401) is None
