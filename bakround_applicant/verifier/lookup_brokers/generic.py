__author__ = "natesymer"

import json
from datetime import timedelta, datetime
from django.utils import timezone
from bakround_applicant.all_models.db import Profile, ProfileReverseLookup

class AmbiguousLookupException(Exception):
    pass

class UnexpectedOutputException(Exception):
    pass

class LookupFailedException(Exception):
    pass

class GenericLookupBroker:
    """Generic class for looking up people on the internet."""

    # In your subclass, set these to true if the data source
    provides_phones = False
    provides_emails = False
    provides_addresses = False
    provides_gender = False
    provides_employment = False
    provides_education = False
    provides_skills = False
    provides_certifications = False

    # Name your provider for DB record keeping's sake
    provider = "generic"

    # __init__()

    def __init__(self,
                 profile = None,
                 reverse_lookup = None,
                 require_emails = False,
                 require_phones = False,
                 require_addresses = False,
                 require_gender = False,
                 require_employment = False,
                 require_education = False,
                 require_skills = False,
                 require_certifications = False,
                 use_cache = True):
        self.use_cache = use_cache
        self.profile = None
        self.reverse_lookup = None
        if profile:
            self.profile = profile

        if reverse_lookup:
            if reverse_lookup.provider != self.provider:
                return ValueError("{}.__init__(): provider mismatch: Unexpected ProfileReverseLookup id {} provider {}. Expected provider {}.".format(type(self), reverse_lookup.id, reverse_lookup.provider, self.provider))
            if not self.profile:
                self.profile = reverse_lookup.profile
            self.reverse_lookup = reverse_lookup

        self.require_addresses = require_addresses
        self.require_emails = require_emails
        self.require_phones = require_phones
        self.require_gender = require_gender
        self.require_employment = require_employment
        self.require_education = require_education
        self.require_skills = require_skills
        self.require_certifications = require_certifications

        self._emails = None
        self._phones = None
        self._addresses = None
        self._gender = None
        self._employment = None
        self._education = None
        self._skills = None
        self._certifications = None

    # Public API

    @property
    def emails(self):
        if not self.provides_emails:
            if self.require_emails:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._emails

    @property
    def phones(self):
        if not self.provides_phones:
            if self.require_phones:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._phones

    @property
    def addresses(self):
        if not self.provides_addresses:
            if self.require_addresses:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._addresses

    @property
    def gender(self):
        if not self.provides_gender:
            if self.require_gender:
                raise AmbiguousLookupException()
            return None
        self._load_data_if_necessary()
        return self._gender

    @property
    def employment(self):
        if not self.provides_employment:
            if self.require_employment:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._employment

    @property
    def education(self):
        if not self.provides_education:
            if self.require_education:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._education

    @property
    def skills(self):
        if not self.provides_skills:
            if self.require_skills:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._skills

    @property
    def certifications(self):
        if not self.provides_certifications:
            if self.require_certifications:
                raise AmbiguousLookupException()
            return []
        self._load_data_if_necessary()
        return self._certifications

    def preload(self):
        """A means of eagerly querying your lookup API."""
        self._load_data_if_necessary()

    # Subclass Override Stubs

    def query_provider(self):
        """Use self.profile to query your data provider and return a parsed JSON response.
           Raise LookupFailedException when appropriate"""
        return {}

    def parse_reverse_lookup(self):
        """Use self.reverse_lookup to return a 3-tuple of (list(emails), list(phones), list(addresses)).
           Raise AmbiguousLookupException and UnexpectedOutputException when appropriate"""
        return ([], [], [])

    # Internal Methods

    def _load_data_if_necessary(self):
        if self._emails is None or self._phones is None or self._addresses is None:
            self._load_data()

    def _load_data(self):
        if self.use_cache and not self.reverse_lookup:
            lookup = ProfileReverseLookup.objects.filter(profile_id=self.profile.id).order_by("-date_created").first()
            if lookup and lookup.date_created > (timezone.now() - timedelta(days=30)):
                self.reverse_lookup = lookup

        if not self.reverse_lookup:
            json_result = self.query_provider()
            prl = ProfileReverseLookup(profile=self.profile, provider=self.provider, output=json_result)
            prl.save()
            self.reverse_lookup = prl

        # In case we're using a lookup that had its output incorrectly set.
        if isinstance(self.reverse_lookup.output, str):
            self.reverse_lookup.output = json.loads(self.reverse_lookup.output)
            self.reverse_lookup.save()

        d = self.parse_reverse_lookup()
        self._emails = d.get("emails") or []
        self._phones = d.get("phones") or []
        self._addresses = d.get("addresses") or []
        self._gender = d.get("gender")
        self._employment = d.get("employment") or []
        self._education = d.get("education") or []
        self._skills = d.get("skills") or []
        self._certifications = d.get("certifications") or []

        if self.require_phones and not self._phones:
            raise AmbiguousLookupException()

        if self.require_emails and not self._emails:
            raise AmbiguousLookupException()

        if self.require_addresses and not self._addresses:
            raise AmbiguousLookupException()

