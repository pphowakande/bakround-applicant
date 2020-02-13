__author__ = "natesymer"

import json
import os
from datetime import date

###############################

from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact, verify_sane
from bakround_applicant.verifier.lookup_brokers import AmbiguousLookupException, \
                                                       UnexpectedOutputException, LookupFailedException
from bakround_applicant.services.queue import QueueNames
from bakround_applicant.all_models.db import Profile, ProfileResume, ProfileEmail, \
                                             ProfilePhoneNumber, ProfileVerificationRequest, \
                                             LookupState, LookupCountry

#################################


from piplapis.search import SearchAPIRequest

from .generic import GenericLookupBroker, LookupFailedException, UnexpectedOutputException, AmbiguousLookupException

class PiplLookupBroker(GenericLookupBroker):
    provides_phones = True
    provides_emails = True
    provides_addresses = True
    provides_gender = True

    # TODO: these two will be set up in the future
    provides_education = False
    provides_employment = True

    provider = "pipl"

    def query_provider(self):
        return call_pipl(profile=self.profile)

    def standardize_address(self, address_dict):
        house = address_dict.get("house")
        street = address_dict.get("street")
        country = address_dict.get("country")
        state = address_dict.get("state")
        return dict(
            street_address="{} {}".format(house, street),
            state=LookupState.objects.filter(state_code=state).first(),
            city=address_dict.get("city"),
            country=LookupCountry.objects.filter(country_code=country).first()
        )

    def standardize_job(self, job_dict):
        start_date = job_dict.get("start_date") or None
        if start_date:
            start_date = date.strptime(start_date, "%Y-%m-%d") or None

        end_date = job_dict.get("end_date") or None
        if end_date:
            end_date = date.strptime(end_date, "%Y-%m-%d") or None

        return dict(
            title=job_dict.get("title") or None,
            industry=job_dict.get("industry") or None,
            start_date=start_date,
            end_date=end_date
        )

    def standardize_education(self, edu_dict):
        return edu_dict

    def parse_reverse_lookup(self):
        lookup = self.reverse_lookup.output
        if not lookup:
            raise AmbiguousLookupException()

        person = lookup.get("person")
        persons_count = lookup.get("@persons_count")
        
        if persons_count == 0:
            print("Ambiguous Lookup: No people")
            raise AmbiguousLookupException()
        elif persons_count == 1:
            if person:
                return dict(emails=list(map(lambda d: d.get("address"), person.get("emails") or [])),
                            phones=list(map(lambda d: d.get("number"), person.get("phones") or [])),
                            addresses=list(map(self.standardize_address, person.get("addresses") or [])),
                            gender=person.get("gender", {}).get("content"),
                            employment=list(map(self.standardize_job, person.get("jobs") or [])),
                            education=list(map(self.standardize_education, person.get("educations") or [])))

        raise AmbiguousLookupException()

def call_pipl(profile=None, search_pointer=None):
    api_key = os.environ.get("PIPL_API_KEY")

    if not api_key:
        print("call_pipl(): Warning: Missing API Key.")

    params = { 'api_key': api_key, 'hide_sponsored': True, 'use_https': True }

    if search_pointer:
        params["search_pointer"] = search_pointer
    elif profile:
        # TODO: Look into using advanced search:
        # https://docs.pipl.com/reference/#using-search-parameters

        # TODO: look this up from the profile
        params['country'] = 'US'

        email = ProfileEmail.to_reach(profile.id, strict=True)
        if email:
            params["email"] = email.value

        if profile.state_id:
            params["state"] = profile.state.state_code

        if profile.city:
            params["city"] = profile.city

        if profile.first_name:
            params["first_name"] = profile.first_name

        if profile.last_name:
            params["last_name"] = profile.last_name
    else:
        print("Abiguous Lookup: Not enough information to make a PIPL query.")
        raise AmbiguousLookupException()

    try:
        response = SearchAPIRequest(**params).send()
    except ValueError: # ValueError's get raised when there's not enough information in the query
        print("Sparse PIPL query.")
        raise AmbiguousLookupException()

    if response and response.http_status_code == 200:
        if response.persons_count > 1:
           print("Ambiguous Lookup: Too many results")
           raise AmbiguousLookupException()
           # NS 11.13.18 - disable because search pointer logic is FUBAR
           # search_pointer = get_valid_search_pointer_from_pipl_response(response, job=profile.job)
           # if search_pointer:
           #     return call_pipl(search_pointer=search_pointer)
        return json.loads(response.raw_json.replace('\n', ''))
    else:
        print("Bad HTTP response.")
        raise LookupFailedException()
    
    return None

#
#
#
# TODODODO: FIX ME NOW
#
#
#
# NOTA BENE: this code was carried over unmodified from the old iteration of the notification service.
#            It also implements some business logic that is semi-relevant (hospitality - irrelevant, RN - relevant).
# FIXME: Please fix the generation of `terms_to_search` as listed above
def get_valid_search_pointer_from_pipl_response(response, job=None, job_family_name=''):
    if job and job.job_family:
        job_family_name = job.job_family.family_name

    if job_family_name.lower() == 'hospitality':
        terms_to_search = [{'term': 'restaurant'},
                           {'term': 'bartender'},
                           {'term': 'server'},
                           {'term': 'host'},
                           {'term': 'cook'}]
    else:
        terms_to_search = [{'term': 'RN', 'preserve_case': True},
                           {'term': 'nurse'},
                           {'term': 'nursing'}]

    try:
        ptrs = []
        for person in response.possible_persons:
            for job in person.jobs:
                for term_obj in terms_to_search:
                    term = term_obj['term']
                    preserve_case = True if 'preserve_case' in term_obj and term_obj['preserve_case'] else False
                    job_title = job.title if job.title is None or preserve_case else job.title.lower()
                    job_industry = job.industry if job.industry is None or preserve_case else job.industry.lower()
                    job_display = job.display if job.display is None or preserve_case else job.display.lower()
                    if (job_title is not None and term in job_title) \
                            or (job_industry is not None and term in job_industry) \
                            or (job_display is not None and term in job_display):
                        ptrs.append(person.search_pointer)
    except:
        pass
    
    if ptrs and len(ptrs) == 1:
        return ptrs[0]

    return None
