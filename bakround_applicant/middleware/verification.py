
__author__ = "tplick"

# If a user is awaiting verification, log him out during any request.


from django.contrib.auth import logout
from bakround_applicant.all_models.db import Profile, EmailAddress
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact

class VerificationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and
                is_user_awaiting_verification(request.user)):
            logout(request)

        return self.get_response(request)


def is_user_awaiting_verification(user):
    try:
        profile = Profile.objects.filter(user=user, queued_for_deletion=False).first()

        collect_contact_info_for_profile(profile)
        email = ProfileEmail.to_reach(profile.id, strict=True)

        return profile and email and EmailAddress.objects.filter(email=email, verified=False).exists()
    except Exception:
        return False
