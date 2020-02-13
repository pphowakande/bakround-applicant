# 28 February 2017

__author__ = "tplick"

import requests
import json
import datetime
from ..all_models.db import User, Profile, SocialAccount, SocialToken


LINKEDIN_PROFILE_FIELDS = [
    "id", "first-name", "last-name",
    "maiden-name", "formatted-name",
    "phonetic-first-name", "phonetic-last-name", "formatted-phonetic-name",
    "headline", "location", "industry", "current-share",
    "num-connections", "num-connections-capped",
    "summary", "specialties", "positions",
    "picture-url", "picture-urls::(original)",
    "site-standard-profile-request", "api-standard-profile-request", "public-profile-url"
]
LINKEDIN_PROFILE_FIELDS_AS_STRING = ','.join(LINKEDIN_PROFILE_FIELDS)

LINKEDIN_URL_FORMAT = \
    "https://api.linkedin.com/v1/people/~:({})?oauth2_access_token={}&format=json"


def load_linkedin_info_for_user(user_obj=None, user_id=None):
    if user_id:
        user_obj = User.objects.get(id=user_id)

    social_account_obj = SocialAccount.objects.filter(
                                user=user_obj, provider="linkedin_oauth2").order_by('id').last()
    social_token_obj = SocialToken.objects.filter(
                                account=social_account_obj).order_by('id').last()

    if social_token_obj and social_token_obj.token:
        return get_linkedin_info_for_token(social_token_obj.token)


def get_linkedin_info_for_token(token):
    url = LINKEDIN_URL_FORMAT.format(LINKEDIN_PROFILE_FIELDS_AS_STRING, token)
    return requests.get(url).json()



if __name__ == '__main__':
    import sys
    token = sys.argv[1]

    from django.conf import settings
    print(get_linkedin_info_for_token(token))
