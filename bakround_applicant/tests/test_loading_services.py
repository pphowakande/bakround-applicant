
import pytest
import importlib

SERVICES = ["buildprofile", "scrapingservice", "verifyingservice", "notificationservice",
            "ondemandviewrefresherservice", "onetcopyservice", "profiledeletionservice",
            "scoringservice"]


@pytest.mark.django_db
def test_loading_services():
    for service in SERVICES:
        try_to_load_service(service)


def try_to_load_service(service):
    module_name = 'bakround_applicant.services.{}.consumer'.format(service)
    module = importlib.import_module(module_name)
    assert module is not None
    assert module.Consumer is not None
