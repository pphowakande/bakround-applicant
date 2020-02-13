__author__ = "natesymer"

from marshmallow import Schema, fields, pprint, post_load

from bakround_applicant.lookup.models import LookupState
from bakround_applicant.utilities.helpers.models import find_levenshtein

#
# ProfileResume
#

class Experience(object):
    company_name = None
    job_title = None
    job_description = None
    city_name = None
    state_code = None
    country_code = None
    start_date = None
    end_date = None
    is_current_position = False

    def __init__(self, **kwargs):
        self.company_name = kwargs.get('company_name')
        self.job_title = kwargs.get('job_title')
        self.job_description = kwargs.get('job_description')
        self.city_name = kwargs.get('city_name')
        self.state_code = kwargs.get('state_code')
        self.country_code = kwargs.get('country_code')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.is_current_position = kwargs.get('is_current_position') or False

class ExperienceSchema(Schema):
    company_name = fields.Str(allow_none=True)
    job_title = fields.Str(allow_none=True)
    job_description = fields.Str(allow_none=True)
    city_name = fields.Str(allow_none=True)
    state_code = fields.Str(allow_none=True)
    country_code = fields.Str(allow_none=True)
    start_date = fields.Str(allow_none=True)
    end_date = fields.Str(allow_none=True)
    is_current_position = fields.Bool(allow_none=True)

    @post_load
    def make_object(self, data):
        return Experience(**data)

class Education(object):
    school_type = None
    school_name = None
    degree_name = None
    degree_major = None
    degree_type = None
    degree_date = None
    city_name = None
    state_code = None
    country_code = None
    start_date = None
    end_date = None

    def __init__(self, **kwargs):
        self.school_type = kwargs.get('school_type')
        self.school_name = kwargs.get('school_name')
        self.degree_name = kwargs.get('degree_name')
        self.degree_major = kwargs.get('degree_major')
        self.degree_type = kwargs.get('degree_type')
        self.degree_date = kwargs.get('degree_date')
        self.city_name = kwargs.get('city_name')
        self.state_code = kwargs.get('state_code')
        self.country_code = kwargs.get('country_code')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')

class EducationSchema(Schema):
    school_type = fields.Str(allow_none=True)
    school_name = fields.Str(allow_none=True)
    degree_name = fields.Str(allow_none=True)
    degree_major = fields.Str(allow_none=True)
    degree_type = fields.Str(allow_none=True)
    degree_date = fields.Str(allow_none=True)
    city_name = fields.Str(allow_none=True)
    state_code = fields.Str(allow_none=True)
    country_code = fields.Str(allow_none=True)
    start_date = fields.Str(allow_none=True)
    end_date = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return Education(**data)

class Skill(object):
    skill_name = None
    experience_months = 0
    last_used_date = None

    def __init__(self, **kwargs):
        self.skill_name = kwargs.get('skill_name')
        self.experience_months = kwargs.get('experience_months', 0)
        self.last_used_date = kwargs.get('last_used_date')

class SkillSchema(Schema):
    skill_name = fields.Str(allow_none=True)
    experience_months = fields.Int(allow_none=True)
    last_used_date = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return Skill(**data)

class Certification(object):
    certification_name = None
    issued_date = None

    def __init__(self, **kwargs):
        self.certification_name = kwargs.get('certification_name')
        self.issued_date = kwargs.get('issued_date')


class CertificationSchema(Schema):
    certification_name = fields.Str(allow_none=True)
    issued_date = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return Certification(**data)


class IcimsPhone(object):
    phone_type = None
    phone = None

    def __init__(self, **kwargs):
        self.phone_type = kwargs.get('phone_type')
        self.phone = kwargs.get('phone')

class IcimsPhoneSchema(Schema):
    phone_type = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return IcimsPhone(**data)

class IcimsEmail(object):
    email = None

    def __init__(self, **kwargs):
        self.email = kwargs.get('email')

class IcimsEmailSchema(Schema):
    email = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return IcimsEmail(**data)


class IcimsJob(object):
    value = None
    job = None
    id = None

    def __init__(self, **kwargs):
        self.value = kwargs.get('value')
        self.job = kwargs.get('job')
        self.id = kwargs.get('id')

class IcimsJobSchema(Schema):
    value = fields.Str(allow_none=True)
    job = fields.Str(allow_none=True)
    id = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return IcimsJob(**data)


class ProfileData(object):
    first_name = None
    middle_name = None
    last_name = None
    emails = []
    phones = []
    summary = None
    street_address = None
    city = None
    state_code = None
    experience = []
    education = []
    skills = []
    certifications = []
    icims_job =[]
    icims_phones = []
    icims_email = ""
    last_updated_date = None

    def __init__(self, **kwargs):
        self.first_name = kwargs.get('first_name') or None
        self.middle_name = kwargs.get('middle_name') or None
        self.last_name = kwargs.get('last_name') or None
        self.summary = kwargs.get('summary') or None
        self.street_address = kwargs.get('street_address') or None
        self.city = kwargs.get('city') or None
        self.state_code = kwargs.get('state_code') or None
        self.last_updated_date = kwargs.get('last_updated_date') or None
        self.emails = filter(bool, kwargs.get('emails') or [])
        self.phones = filter(bool, kwargs.get('phones') or [])
        self.skills = filter(bool, kwargs.get('skills') or [])
        self.experience = filter(bool, kwargs.get('experience') or [])
        self.education = filter(bool, kwargs.get('education') or [])
        self.certifications = filter(bool, kwargs.get('certifications') or [])
        self.icims_job = filter(bool, kwargs.get('icims_job') or [])
        self.icims_phones = filter(bool, kwargs.get('icims_phones') or [])
        self.icims_email = kwargs.get('icims_email') or None

class ProfileDataSchema(Schema):
    first_name = fields.Str(allow_none=True)
    middle_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    emails = fields.List(fields.Str(allow_none=False), missing=[])
    phones = fields.List(fields.Str(allow_none=False), missing=[])
    summary = fields.Str(allow_none=True)
    street_address = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    state_code = fields.Str(allow_none=True)
    experience = fields.Nested(ExperienceSchema, many=True)
    education = fields.Nested(EducationSchema, many=True)
    skills = fields.Nested(SkillSchema, many=True) # Really broken. Indeed parser returns a list of strs, not these structures.
    certifications = fields.Nested(CertificationSchema, many=True)
    icims_job = fields.Nested(IcimsJobSchema, many=True)
    icims_phones = fields.Nested(IcimsPhoneSchema, many=True)
    last_updated_date = fields.Str(allow_none=True)
    icims_email = fields.Str(allow_none=True)

    # Deprecated - read, but not written
    phone = fields.Str(allow_none=True) # backwards compat
    email = fields.Str(allow_none=True) # backwards compat
    state = fields.Str(allow_none=True) # backwards compat

    # Deprecated - Unused
    zip_code = fields.Str(allow_none=True) # backwards compat
    location = fields.Str(allow_none=True) # backwards compat
    title = fields.Str(allow_none=True) # backwards compat

    @post_load
    def make_object(self, data):
        if 'email' in data:
            if not data.get('emails'):
                data['emails'] = []
            data['emails'].append(data['email'])
            del data['email']
        if 'phone' in data:
            if not data.get('phones'):
                data['phones'] = []
            data['phones'].append(data['phone'])
            del data['phone']

        if 'state' in data and 'state_code' not in data:
            s = data['state']
            new_state = LookupState.objects.filter(state_code=s).values_list('id', flat=True).first() or find_levenshtein(LookupState, 'state_name', s)
            if new_state:
                data['state_code'] = new_state.state_code
            del data['state']

        for k in ['zip_code', 'location', 'title']:
            if k in data:
                del data[k]

        return ProfileData(**data)

#
# Profile Search
#

class LookupStateField(fields.Raw):
    def _deserialize(self, value, attr, data):
        return self._validated(value)

    def _serialize(self, value, attr, obj):
        if not obj:
            return None
        return obj.state_code

    def _validated(self, value):
        if not value:
            return None

        state_code = str(value).strip().upper()
        try:
            return LookupState.objects.get(state_code=state_code)
        except Exception:
            self.fail('Invalid state')

class ProfileSearchQuery:
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ProfileSearchQuerySchema(Schema):
    job_id = fields.Int(required=True)
    city = fields.Str(required=True)
    state = LookupStateField(required=True)
    employer_job_id = fields.Int(required=True) # Was this meant to be an optional field, defaulting to None?
    page = fields.Int(missing=1)
    page_size = fields.Int(default=20, missing=20, validate=lambda x: x in (20, 50))
    profile_ids_to_exclude = fields.List(fields.Int(), missing=[])
    experience = fields.Int(missing=None) # In months
    score = fields.Int(missing=None)
    distance = fields.Int(missing=100, validate=lambda x: -200 <= x <= 200)
    ordering = fields.Str(missing='score', validate=lambda x: x in ('distance', 'score', 'experience', 'last_updated_date'))
    min_education = fields.Str(missing=None, validate=lambda x: x is None or x in ('highschool', 'associates', 'bachelors', 'masters', 'doctorate'))
    state_filter = fields.Int(missing=None)
    advanced = fields.Dict( missing=None)

    @post_load
    def make_object(self, data):
        data["page"] = data["page"] - 1
        data["city"] = data["city"].strip()
        return ProfileSearchQuery(**data)


class IcimsProfileSearchQuerySchema(Schema):
    job_id = fields.Int(required=True)
    city = fields.Str(required=True)
    state = LookupStateField(required=True)
    icims_job_id = fields.Int(required=True) # Was this meant to be an optional field, defaulting to None?
    page = fields.Int(missing=1)
    page_size = fields.Int(default=20, missing=20, validate=lambda x: x in (20, 50))
    profile_ids_to_exclude = fields.List(fields.Int(), missing=[])
    experience = fields.Int(missing=None) # In months
    score = fields.Int(missing=None)
    distance = fields.Int(missing=100, validate=lambda x: -200 <= x <= 200)
    ordering = fields.Str(missing='score', validate=lambda x: x in ('distance', 'score', 'experience', 'last_updated_date'))
    min_education = fields.Str(missing=None, validate=lambda x: x is None or x in ('highschool', 'associates', 'bachelors', 'masters', 'doctorate'))
    state_filter = fields.Int(missing=None)
    advanced = fields.Dict( missing=None)

    @post_load
    def make_object(self, data):
        data["page"] = data["page"] - 1
        data["city"] = data["city"].strip()
        return ProfileSearchQuery(**data)
