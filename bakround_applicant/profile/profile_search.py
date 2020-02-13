__author__ = "tplick"

import collections
import time
import itertools
from math import pi as PI
from math import sin, cos, acos
import string
import os
import json
from datetime import timedelta

from django.db import connection, models, transaction
from django.db.models import Subquery, OuterRef, Exists, Q, F
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Count, Sum
from django.utils import timezone
from django.core.exceptions import EmptyResultSet

from ..all_models.db import Profile, ProfileExperience, Score, \
                            LookupCountry, LookupState, LookupDegreeType, \
                            ProfileEducation, LookupPhysicalLocation, Skill, Job, \
                            EmployerUser, EmployerJob, EmployerCandidate, EmployerSavedSearch, \
                            EmployerSearchResult, EmployerRestrictedProfile, EmployerProfileView, \
                            EmployerCandidateFeedback, IcimsJobData, IcimsProfileJobMapping
from ..all_models.dto import ProfileSearchQuerySchema, IcimsProfileSearchQuerySchema
from ..event import record_event, EventActions
from ..utilities.functions import take_n_at_a_time, get_website_root_url, is_production, is_dev

from bakround_applicant.utilities.logger import LoggerFactory
logger = LoggerFactory.create('PROFILE_SEARCH')

MAX_RESULTS = 2000
INTERNAL_PAGE_SIZE = 10
assert MAX_RESULTS % INTERNAL_PAGE_SIZE == 0
INTERNAL_MAX_PAGES = MAX_RESULTS // INTERNAL_PAGE_SIZE

MULTI_MATCH_FIELDS = [
    "summary",
    "experience.company_name",
    "experience.position_title",
    "experience.position_description",
    "skills.skill_name",
    "certifications.certification_name",
]

CAPITAL_LETTERS = string.ascii_uppercase

__search_profile = None

# # Candidate structure:
# # This is the format the frontend expects.
# {
#     'candidate_id': 'EmployerCandidate ID',
#     'id': 'SearchProfile/Profile ID',
#     'score': "BScore",
#     "contacted": True,
#     "visible": True,
#     "sourced_by_employer": False,
#     "responded": False,
#     "accepted": False,
#     "first_name": "Foo",
#     "last_name": "Bar",
#     'city': 'Philadelphia',
#     'state': 'PA',
#     'distance': 0, # distance from you
#     'last_updated_date': 'From SearchProfile'
#     "total_experience_months": "From SearchProfile"
# }

# The SearchProfile class allows access to the materialized view through the Django ORM.
# I create it inside this function to prevent Django from making migrations for it.
def make_search_profile_model(cached={}):
    global __search_profile

    if __search_profile is not None:
        return __search_profile

    class SearchProfile(models.Model):
        # id does not have to be defined here, because Django adds it automatically.
        # id = models.IntegerField()

        # From the `profile` table
        first_name = models.TextField()
        last_name = models.TextField()
        city = models.TextField()
        state = models.ForeignKey('lookup.LookupState', null=True)
        last_updated_date = models.DateTimeField(null=True)

        # extra fields added in the view
        scored_job_id = models.IntegerField()
        score_value = models.DecimalField(max_digits=20, decimal_places=10)
        total_experience_months = models.FloatField()

        class Meta:
            managed = False
            db_table = "search_profile_view4"

    __search_profile = SearchProfile
    return __search_profile

# This function is called by the view that handles /profile/search.
def handle_profile_search_request(params, user=None):
    print("Inside handle_profile_search_request function------------------")
    print("params : ", params)
    result = ProfileSearchQuerySchema().load(params)

    if result.errors:
        return {"error": "Invalid search query."}

    query = result.data
    print("query : ", query)

    # record_event(user,
    #              EventActions.employer_job_search,
    #              {'job_id': job_id, 'city': city, 'state': state_code, 'page': page_number,
    #               'advanced_used': advanced is not None})

    query_start_time = time.time()

    try:
        location = get_location_for_city(query.city, query.state)
    except LookupPhysicalLocation.DoesNotExist:
        return {"error": "no location info for {}, {}".format(query.city, query.state)}

    profiles = make_queryset_of_search_profiles(
        job_id=query.job_id,
        location=location,
        distance=query.distance,
        state_filter=query.state_filter,
        profile_ids_to_exclude=query.profile_ids_to_exclude,
        min_education=query.min_education,
        ordering=query.ordering,
        experience=query.experience,
        score=query.score,
        advanced=query.advanced,
        employer_job_id=query.employer_job_id
    )

    print("profiles : ", profiles)

    num_results = profiles.count()
    print("num_results : ", num_results)

    # TODO: include an EmployerUser in this subquery. It doesn't matter if it's just Kate using the
    # system, but it really matters when multiple people are using it.
    profile_views = EmployerProfileView.objects.filter(employer_job_id=query.employer_job_id,
                                                       profile_id=OuterRef("id")).values("id")
    profiles = profiles.annotate(previously_viewed=Exists(profile_views))

    start_offset = query.page * query.page_size
    profiles = profiles[start_offset : start_offset + query.page_size]

    query_time = time.time() - query_start_time
    logger.info("Query Time: {}".format(query_time))

    return {
        **convert_page_to_json(query.page, profiles),
        "distance": query.distance,
        "ordering": query.ordering,
        "query_time": query_time,
        "num_results": num_results
    }

# This function is called by the view that handles /profile/icims_search.
def handle_icims_profile_search_request(params, user=None):
    print("Inside handle_icims_profile_search_request function------------------")
    result = IcimsProfileSearchQuerySchema().load(params)
    print("result : ", result)

    if result.errors:
        return {"error": "Invalid search query."}

    print("result.data : ", result.data)
    query = result.data
    print("query : ", query)

    # record_event(user,
    #              EventActions.employer_job_search,
    #              {'job_id': job_id, 'city': city, 'state': state_code, 'page': page_number,
    #               'advanced_used': advanced is not None})

    query_start_time = time.time()

    try:
        print("inside if loop")
        location = ''
        print("location : ", location)
    except LookupPhysicalLocation.DoesNotExist:
        print("inside exception")
        return {"error": "no location info for {}, {}".format(query.city, query.state)}


    print("making query set----------------")
    profiles = make_queryset_of_search_icims_profiles(
        job_id=query.job_id,
        distance=query.distance,
        state_filter=query.state_filter,
        profile_ids_to_exclude=query.profile_ids_to_exclude,
        min_education=query.min_education,
        ordering=query.ordering,
        experience=query.experience,
        score=query.score,
        advanced=query.advanced,
        icims_job_id=query.icims_job_id
    )

    print("profiles : ", profiles)

    num_results = profiles.count()
    print("num_results : ", num_results)

    # TODO: include an EmployerUser in this subquery. It doesn't matter if it's just Kate using the
    # system, but it really matters when multiple people are using it.
    # profile_views = EmployerProfileView.objects.filter(employer_job_id=query.icims_job_id,
    #                                                    profile_id=OuterRef("id")).values("id")
    # print("profile_views : ", profile_views)
    # profiles = profiles.annotate(previously_viewed=Exists(profile_views))
    # print("profiles before : ", profiles)
    #
    # start_offset = query.page * query.page_size
    # profiles = profiles[start_offset : start_offset + query.page_size]
    # print("profiles after : ", profiles)

    query_time = time.time() - query_start_time
    logger.info("Query Time: {}".format(query_time))

    return {
        **convert_page_to_json(query.page, profiles),
        "distance": query.distance,
        "ordering": query.ordering,
        "query_time": query_time,
        "num_results": num_results
    }


def make_queryset_of_search_profiles(job_id=None,location=None,distance=None,state_filter=None,profile_ids_to_exclude=None,min_education=None,ordering=None,experience=None,score=None,advanced=None,employer_job_id=None):
    SearchProfile = make_search_profile_model()
    print("SearchProfile : ", SearchProfile)

    scored_job_id = job_id
    print("scored_job_id : ", scored_job_id)
    if not Job.objects.get(id=job_id).has_ever_been_scored:
        scored_job_id = get_parent_job_id_of_job(job_id) or job_id

    profiles = SearchProfile.objects.filter(scored_job_id=scored_job_id).defer('scored_job_id')
    print("profiles : ", profiles)

    # Don't show restricted profiles to people who shouldn't see them
    employer_id = EmployerJob.objects.get(id=employer_job_id).employer_id
    print("employer_id : ", employer_id)
    restricted_profile_ids = (list(EmployerRestrictedProfile.objects
                                                            .filter(employer_id=employer_id)
                                                            .values_list('profile_id', flat=True)))
    if restricted_profile_ids:
        profiles = profiles.exclude(id__in=restricted_profile_ids)

    # enforce minimum experience requirement
    if experience is not None:
        profiles = profiles.filter(total_experience_months__gte=experience)

    # enforce minimum score requirement
    if score is not None:
        profiles = profiles.filter(score_value__gte=score)

    # state_filter
    if state_filter:
        profiles = profiles.filter(state_id=state_filter)

    # restrict to profiles within (distance) miles of center
    if location:
        latitude, longitude = location.latitude, location.longitude
        profiles = annotate_profiles_with_distance(profiles, (latitude, longitude))
        if distance:
            profiles = filter_profiles_by_distance(profiles, (latitude, longitude), distance)

    # enforce minimum education requirement
    if min_education:
        profiles = filter_profiles_by_education(profiles, min_education)

    # TODO: advanced search in Postgres via TSVector (using query.advanced)

    # Already added to our job? Hide from search results.
    if employer_job_id:
        profiles = profiles.exclude(id__in=EmployerCandidate.objects.filter(employer_job_id=employer_job_id).values("profile_id"))
        profiles = profiles.annotate(feedback=Subquery(EmployerCandidateFeedback.objects.filter(profile_id=OuterRef("id"), employer_job_id=employer_job_id).values_list("bscore_value", flat=True)))

    # sort profiles by distance
    if ordering == 'distance':
        profiles = profiles.order_by(F('distance').desc(nulls_last=True)) # TODO: for negative distances, reverse order
    elif ordering == 'experience':
        profiles = profiles.order_by(F('total_experience_months').desc(nulls_last=True))
    elif ordering == 'score':
        profiles = profiles.order_by(F('score_value').desc(nulls_last=True))
    elif ordering == 'last_updated_date':
        profiles = profiles.order_by(F('last_updated_date').desc(nulls_last=True))

    print("profiles final---------: ", profiles)
    return profiles


def make_queryset_of_search_icims_profiles(job_id=None,location=None,distance=None,state_filter=None,profile_ids_to_exclude=None,min_education=None,ordering=None,experience=None,score=None,advanced=None,icims_job_id=None):
    print("make_queryset_of_search_icims_profiles -------------")
    SearchProfile = make_search_profile_model()

    scored_job_id = job_id
    print("scored_job_id : ", scored_job_id)
    # if not Job.objects.get(id=job_id).has_ever_been_scored:
    #     scored_job_id = get_parent_job_id_of_job(job_id) or job_id

    # get bakround job id which was mapped against icims job id nd use that
    bakround_job_id = IcimsProfileJobMapping.objects.filter(icims_job_id_id=scored_job_id).first()
    print("bakround_job_id : ", bakround_job_id)

    profiles = SearchProfile.objects.filter(scored_job_id=bakround_job_id.job_id).defer('scored_job_id')
    print("profiles : ", profiles)
    # # Don't show restricted profiles to people who shouldn't see them
    # employer_id = IcimsJobData.objects.get(id=icims_job_id).id
    # print("employer_id : ", employer_id)
    # restricted_profile_ids = (list(EmployerRestrictedProfile.objects
    #                                                         .filter(employer_id=employer_id)
    #                                                         .values_list('profile_id', flat=True)))
    # if restricted_profile_ids:
    #     profiles = profiles.exclude(id__in=restricted_profile_ids)

    # enforce minimum experience requirement
    if experience is not None:
        profiles = profiles.filter(total_experience_months__gte=experience)

    # enforce minimum score requirement
    if score is not None:
        profiles = profiles.filter(score_value__gte=score)

    # state_filter
    if state_filter:
        profiles = profiles.filter(state_id=state_filter)

    # restrict to profiles within (distance) miles of center
    if location:
        latitude, longitude = location.latitude, location.longitude
        profiles = annotate_profiles_with_distance(profiles, (latitude, longitude))
        if distance:
            profiles = filter_profiles_by_distance(profiles, (latitude, longitude), distance)

    # enforce minimum education requirement
    if min_education:
        profiles = filter_profiles_by_education(profiles, min_education)

    # TODO: advanced search in Postgres via TSVector (using query.advanced)

    # Already added to our job? Hide from search results.
    if icims_job_id:
        profiles = profiles.exclude(id__in=EmployerCandidate.objects.filter(employer_job_id=icims_job_id).values("profile_id"))
        profiles = profiles.annotate(feedback=Subquery(EmployerCandidateFeedback.objects.filter(profile_id=OuterRef("id"), employer_job_id=icims_job_id).values_list("bscore_value", flat=True)))

    # sort profiles by distance
    if ordering == 'distance':
        profiles = profiles.order_by(F('distance').desc(nulls_last=True)) # TODO: for negative distances, reverse order
    elif ordering == 'experience':
        profiles = profiles.order_by(F('total_experience_months').desc(nulls_last=True))
    elif ordering == 'score':
        profiles = profiles.order_by(F('score_value').desc(nulls_last=True))
    elif ordering == 'last_updated_date':
        profiles = profiles.order_by(F('last_updated_date').desc(nulls_last=True))

    print("profiles final---------: ", profiles)
    return profiles


def list_candidates_for_job(employer_job_id, page_number, page_size, args = {}, ordering = 'score'):
    """Get a single page's worth of EmployerCandidates. Return as a list of dicts ready for JSON."""

    wheres = []
    if 'contacted' in args:
        wheres.append('ec."contacted"={}'.format("'t'" if args['contacted'] else "'f'"))
    if 'accepted' in args:
        wheres.append('ec."accepted"={}'.format("'t'" if args['accepted'] else "'f'"))
    if 'responded' in args:
        wheres.append('ec."responded"={}'.format("'t'" if args['responded'] else "'f'"))

    # We drop down to SQL here because Django makes egregiously ineffecient queries
    # when dealing with two "unofficially related" tables.
    #
    # Note the ON part of the query. We need both fields to effectively use
    # the index named search_profile_view__pk_id

    ordering_to_column = {
        'score': 'p."score_value"',
        'distance': 'distance',
        'total_experience_months': 'p."total_experience_months"',
        'last_updated_date': 'p."last_updated_date"',
        'contact_date_for_ordering': 'ec."contacted_date"',
        'response_date_for_ordering': 'ec."contacted_date"'
    }

    ordering_col = ordering_to_column.get(ordering, ordering_to_column['score'])

    employer_job = EmployerJob.objects.get(id=employer_job_id)
    location = get_location_for_city(employer_job.city, employer_job.state)
    distance_expr = get_distance_expression((location.latitude, location.longitude))

    job = employer_job.job
    scored_job_id = job.id
    if not job.has_ever_been_scored:
        scored_job_id = get_parent_job_id_of_job(job.id) or job.id

    query = """
        SELECT ec."id" as candidate_id,
               ec."profile_id" as id,
               ec."contacted",
               ec."visible",
               ec."sourced_by_employer",
               ec."responded",
               ec."accepted",
               p."first_name",
               p."last_name",
               (SELECT ls."state_code" FROM lookup_state ls WHERE ls."id"=p."state_id" LIMIT 1) as state,
               (SELECT ecf."bscore_value" FROM employer_candidate_feedback ecf WHERE ecf."profile_id"=p."id" AND ecf."employer_job_id"=ec."employer_job_id" ORDER BY ecf."id" DESC LIMIT 1) as feedback,
               (SELECT lcs."status" FROM employer_candidate_status ecs INNER JOIN lookup_candidate_status lcs ON lcs."id"=ecs."candidate_status_id" WHERE ecs."employer_candidate_id"=ec."id" ORDER BY ecs.id DESC LIMIT 1) as candidate_status_text,
               p."city",
               p."last_updated_date",
               p."score_value",
               p."total_experience_months",
               {} as distance
        FROM employer_candidate ec
        JOIN search_profile_view4 p
        ON p."id"=ec."profile_id" AND p."scored_job_id"=%s
        WHERE
          ec."employer_job_id"=%s
          {} {}
        ORDER BY {} DESC NULLS FIRST
        LIMIT %s
        OFFSET %s
    """.format(distance_expr, 'AND' if len(wheres) > 0 else '', ' AND '.join(wheres), ordering_col)

    queryset = EmployerCandidate.objects.raw(query, [scored_job_id, employer_job_id, page_size, (page_number * page_size)])

    candidates = []
    for candidate in queryset:
        d = candidate.__dict__
        d['last_updated_date'] = convert_datetime_for_json(d['last_updated_date'])
        d['initials'] = make_initials_for_profile_id(d["id"])
        d['score'] = convert_decimal_to_float(d['score_value'])
        d['feedback'] = convert_decimal_to_float(d['feedback'])
        del d['score_value']
        del d['_state']
        candidates.append(d)

    return candidates

def list_candidates_for_icims_job(icims_job_id, page_number, page_size, args = {}, ordering = 'score'):
    """Get a single page's worth of EmployerCandidates. Return as a list of dicts ready for JSON."""

    wheres = []
    if 'contacted' in args:
        wheres.append('ec."contacted"={}'.format("'t'" if args['contacted'] else "'f'"))
    if 'accepted' in args:
        wheres.append('ec."accepted"={}'.format("'t'" if args['accepted'] else "'f'"))
    if 'responded' in args:
        wheres.append('ec."responded"={}'.format("'t'" if args['responded'] else "'f'"))

    # We drop down to SQL here because Django makes egregiously ineffecient queries
    # when dealing with two "unofficially related" tables.
    #
    # Note the ON part of the query. We need both fields to effectively use
    # the index named search_profile_view__pk_id

    ordering_to_column = {
        'score': 'p."score_value"',
        'distance': 'distance',
        'total_experience_months': 'p."total_experience_months"',
        'last_updated_date': 'p."last_updated_date"',
        'contact_date_for_ordering': 'ec."contacted_date"',
        'response_date_for_ordering': 'ec."contacted_date"'
    }

    ordering_col = ordering_to_column.get(ordering, ordering_to_column['score'])

    icims_job = IcimsJobData.objects.get(id=icims_job_id)
    distance_expr = ''
    print("distance_expr : ", distance_expr)
    job = icims_job
    scored_job_id = job.id

    print("building query")
    query = """
        SELECT ec."id" as candidate_id,
               ec."profile_id" as id,
               ec."contacted",
               ec."visible",
               ec."sourced_by_employer",
               ec."responded",
               ec."accepted",
               p."first_name",
               p."last_name",
               (SELECT ls."state_code" FROM lookup_state ls WHERE ls."id"=p."state_id" LIMIT 1) as state,
               (SELECT ecf."bscore_value" FROM employer_candidate_feedback ecf WHERE ecf."profile_id"=p."id" AND ecf."employer_job_id"=ec."employer_job_id" ORDER BY ecf."id" DESC LIMIT 1) as feedback,
               (SELECT lcs."status" FROM employer_candidate_status ecs INNER JOIN lookup_candidate_status lcs ON lcs."id"=ecs."candidate_status_id" WHERE ecs."employer_candidate_id"=ec."id" ORDER BY ecs.id DESC LIMIT 1) as candidate_status_text,
               p."city",
               p."last_updated_date",
               p."score_value",
               p."total_experience_months"
        FROM employer_candidate ec
        JOIN search_profile_view4 p
        ON p."id"=ec."profile_id" AND p."scored_job_id"=%s
        WHERE
          ec."employer_job_id"=%s
          {} {}
        ORDER BY {} DESC NULLS FIRST
        LIMIT %s
        OFFSET %s
    """.format('AND' if len(wheres) > 0 else '', ' AND '.join(wheres), ordering_col)

    print("query : ", query)
    queryset = EmployerCandidate.objects.raw(query, [scored_job_id, icims_job_id, page_size, (page_number * page_size)])
    print("queryset : ", queryset)
    candidates = []
    for candidate in queryset:
        d = candidate.__dict__
        d['last_updated_date'] = convert_datetime_for_json(d['last_updated_date'])
        d['initials'] = make_initials_for_profile_id(d["id"])
        d['score'] = convert_decimal_to_float(d['score_value'])
        d['feedback'] = convert_decimal_to_float(d['feedback'])
        del d['score_value']
        del d['_state']
        candidates.append(d)
    print("candidates : ", candidates)
    return candidates

def get_location_for_city(city, state):
    return LookupPhysicalLocation.objects.get(city=city, state=state)

def get_distance_expression(center):
    center_latitude, center_longitude = center

    assert isinstance(center_latitude, (int, float))
    assert isinstance(center_longitude, (int, float))

    # LEAST(1, NULL) returns 1, which we don't want.  So we check for a null latitude explicitly.
    return """
            3959 * acos( CASE WHEN latitude IS NULL then NULL
            ELSE LEAST(1, cos( radians({center_latitude}) ) * cos( radians( latitude ) ) *
            cos( radians( longitude ) - radians({center_longitude}) ) + sin( radians({center_latitude}) ) *
            sin( radians( latitude ) )) END)
                """.strip().format(center_latitude=center_latitude,
                                   center_longitude=center_longitude)

def annotate_profiles_with_distance(profiles, center):
    return profiles.extra(select = {"distance": get_distance_expression(center)})

def filter_profiles_by_distance(profiles, center, radius):
    operator = "<=" if radius > 0 else ">="

    radius = abs(radius)

    center_latitude, center_longitude = center

    distance_expression = get_distance_expression(center)

    # tplick, 20 March 2017:
    #   To help Postgres, we calculate a bound on the possible latitudes that we
    #   can have for this distance.  See http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
    #   for the math.  We can also do something with the longitude, but I am leaving that for later.
    max_latitude_variation_for_distance = radius / (PI / 180 * 3959)
    minimum_latitude = center_latitude - max_latitude_variation_for_distance
    maximum_latitude = center_latitude + max_latitude_variation_for_distance

    profiles = profiles.extra(
        where = [
            "{} {} {}".format(distance_expression, operator, radius),
            "latitude BETWEEN {} AND {}".format(minimum_latitude, maximum_latitude),
        ]
    )

    return profiles

def convert_profile_to_json(profile):
    fields = ["id", "first_name", "last_name", "city",
              "contacted", "visible", "sourced_by_employer",
              "responded", "accepted", "candidate_id",
              "employer_id", "distance", "total_experience_months",

              "profile_id",
              "score", "status_updated_date", "last_updated_date", "score_value", 'state_code', 'state', 'state_id']

    if (isinstance(profile, dict)):
        mapping = profile
    else:
        mapping = profile.__dict__

    mapping["contacted"] = False
    mapping["visible"] = True
    mapping["sourced_by_employer"] = False
    mapping["responded"] = False
    mapping["accepted"] = False
    mapping['initials'] = make_initials_for_profile_id(mapping["id"])

    if '_state' in mapping:
        del mapping['_state']

    if 'state_code' in mapping:
        mapping['state'] = mapping["state_code"]
        del mapping['state_code']
    elif 'state_id' in mapping:
        lookup_state = LookupState.objects.filter(id=mapping['state_id']).first()
        if lookup_state:
            mapping['state'] = lookup_state.state_code
        del mapping['state_id']

    if 'score_value' in mapping:
        if mapping['score_value']:
            mapping['score'] = mapping['score_value']
        del mapping['score_value']

    if 'score' in mapping:
        mapping['score'] = convert_decimal_to_float(mapping["score"])

    if 'last_updated_date' in mapping:
        mapping['last_updated_date'] = convert_datetime_for_json(mapping['last_updated_date'])
    if 'status_updated_date' in mapping:
        mapping['status_updated_date'] = convert_datetime_for_json(mapping['status_updated_date'])

    return mapping

def now():
    return timezone.now()

def convert_page_to_json(page_number, page, is_last_page = False, serialize=True):
    return {
        "page_number": page_number+1,
        "page_size": len(page),
        "profiles": list(map(convert_profile_to_json, page)) if serialize else list(page),
        "is_last_page": is_last_page
    }

def convert_decimal_to_float(decimal):
    if decimal is None:
        return None

    return float(decimal)

# Store cached results of database queries.  We cannot compute this at the module scope
#    because the file is loaded before the database connection exists.
def get_lookups(lookups={}):
    if len(lookups) < 2:
        us = LookupCountry.objects.get(country_code='US')
        lookups['state_codes'] = {state.id: state.state_code
                                  for state in LookupState.objects.filter(country=us)}
        lookups['degree_type_ids'] = determine_degree_type_ids_for_education()

    return lookups

def convert_datetime_for_json(dt):
    if dt is None:
        return
    return dt.isoformat()

def get_lookup(key):
    return get_lookups()[key]

def determine_degree_type_ids_for_education():
    degree_ids = {}
    add_degree_ids(degree_ids, 'doctorate', ['doctorate', 'postdoctorate'])
    add_degree_ids(degree_ids, 'masters', ['masters'], include='doctorate')
    add_degree_ids(degree_ids, 'bachelors', ['bachelors'], include='masters')
    add_degree_ids(degree_ids, 'associates', ['associates'], include='bachelors')
    add_degree_ids(degree_ids, 'highschool', ['high school or equivalent', 'ged'], include='associates')
    return degree_ids

def add_degree_ids(degree_ids, query_key, sovren_degree_types, include=None):
    degree_ids[query_key] = [degree_type.id for degree_type in
                             LookupDegreeType.objects.filter(degree_type_sovren__in=sovren_degree_types)
                                                     .order_by('id')]
    if include:
        degree_ids[query_key] += degree_ids[include]

    logger.debug('obtained degree ids for {}: {}'.format(query_key, degree_ids[query_key]))

def filter_profiles_by_education(profiles, min_education):
    degree_type_ids = get_lookup('degree_type_ids')[min_education]
    logger.debug('restricting results to min_education {}; valid degree ids are {}'.format(
                    min_education, degree_type_ids))

    # Return the profiles that have an education entry whose ID is in degree_type_ids.
    # We find the matching profiles by going through the ProfileEducation records.
    profile_ids_with_matching_education = \
        ProfileEducation.objects.filter(degree_type_id__in=degree_type_ids).values('profile_id').distinct()
    return profiles.filter(id__in=profile_ids_with_matching_education)

def max_education_from_education_types(education_types):
    if 'doctorate' in education_types or 'postdoctorate' in education_types:
        return 'doctorate'
    elif 'masters' in education_types:
        return 'masters'
    elif 'bachelors' in education_types:
        return 'bachelors'
    elif 'associates' in education_types:
        return 'associates'
    elif 'high school or equivalent' in education_types or 'ged' in education_types:
        return 'highschool'
    else:
        return None

def to_radians(degrees):
    return degrees / 180.0 * PI

def distance_between_locations(location1, location2):
    return (3959 * acos(cos(to_radians(location1.latitude)) * cos(to_radians(location2.latitude)) *
            cos(to_radians(location2.longitude) - to_radians(location1.longitude)) +
            sin(to_radians(location1.latitude)) * sin(to_radians(location2.latitude))))

def distance_between_cities(city1, state1, city2, state2):
    try:
        location1 = get_location_for_city(city1, state1)
        location2 = get_location_for_city(city2, state2)
        return distance_between_locations(location1, location2)
    except Exception as e:
        logger.exception(e)
        return None

def get_parent_job_id_of_job(job_id):
    return Job.objects.get(id=job_id).parent_job_id

def make_initials_for_profile_id(profile_id):
    digit1 = profile_id % 26
    digit2 = (profile_id // 26) % 26
    return "{}. {}.".format(CAPITAL_LETTERS[digit1],
                            CAPITAL_LETTERS[digit2])
