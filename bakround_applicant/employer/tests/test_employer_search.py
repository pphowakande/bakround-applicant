
__author__ = "tplick"

import pytest
from bakround_applicant.all_models.db import LookupCountry, LookupState, \
                                             LookupPhysicalLocation, \
                                             Profile, Job, Score
from django.core.cache import cache
from django.db import connection
from bakround_applicant.profile.profile_search import distance_between_cities
import importlib
import importlib.util
import importlib.machinery
import types


# tplick, 23 March 2018:
#   profile_search.find_profiles_for_criteria now uses Elasticsearch by default
#   when the web app is run locally.  Because the tests have to run on Jenkins too
#   (where ES is not installed), we override the default setting here, so that
#   the searches run without ES.
from bakround_applicant.profile.profile_search \
    import find_profiles_for_criteria \
    as find_profiles_for_criteria_with_default_search
def find_profiles_for_criteria(*args, **kwargs):
    return find_profiles_for_criteria_with_default_search(*args,
                                                         use_elasticsearch=False,
                                                         **kwargs)


def add_states():
    US = LookupCountry(country_name="United States",
                       country_code="US")
    US.save()

    PA = LookupState(state_name="Pennsylvania",
                     state_code="PA",
                     country=US)
    NJ = LookupState(state_name="New Jersey",
                     state_code="NJ",
                     country=US)
    CA = LookupState(state_name="California",
                     state_code="CA",
                     country=US)

    for state in [PA, NJ, CA]:
        state.save()


def add_cities_and_applicants():
    add_city_and_applicants("Philadelphia", "PA", 39.9522222, -75.1641667,
                            [("Rocky", "Balboa", 1, 1)])
    add_city_and_applicants("Haddonfield", "NJ", 39.8913889, -75.0380556,
                            [("Brad", "Lidge", 1, 2)])
    add_city_and_applicants("San Francisco", "CA", 37.775, -122.4183333,
                            [("Willie", "Mays", 1, 3)])


def add_city_and_applicants(city, state_code, latitude, longitude, applicants):
    state = LookupState.objects.get(state_code=state_code, country_id=1)
    location = LookupPhysicalLocation(
                           city=city,
                           state=state,
                           latitude=latitude,
                           longitude=longitude)
    location.save()

    for (first_name, last_name, job_id, profile_id) in applicants:
        Profile(id=profile_id,
                first_name=first_name,
                last_name=last_name,
                job_id=job_id,
                city=city,
                state=state).save()

def create_search_view():
    data_migration = import_file("0003_data.py")

    with connection.cursor() as cursor:
        cursor.execute(data_migration.SEARCH_PROFILE_VIEW)

def import_file(filename):
    # https://stackoverflow.com/a/67692
    filename = "migrations/" + filename
    spec = importlib.util.spec_from_file_location(filename, filename)

    # this function is not in Python 3.4:
    # module = importlib.util.module_from_spec(spec)

    loader = importlib.machinery.SourceFileLoader(filename, filename)
    module = types.ModuleType(loader.name)

    spec.loader.exec_module(module)
    return module


def refresh_view():
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW search_profile_view")


@pytest.mark.django_db
def test_search():
    create_search_view()

    Job(id=1, job_name="Head of Basketweaving (Underwater Division)").save()
    add_states()
    add_cities_and_applicants()

    PA = LookupState.objects.get(state_code="PA", country_id=1)

    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="Philadelphia",
        state=PA,
        distance=90,
        ordering='distance',
    )
    profiles = results['profiles']

    assert len(profiles) == 2
    assert profiles[0]['last_name'] == "Balboa"
    assert profiles[1]['last_name'] == "Lidge"

    CA = LookupState.objects.get(state_code="CA", country_id=1)

    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="San Francisco",
        state=CA,
        distance=10,
        ordering='score',
    )
    profiles = results['profiles']

    assert len(profiles) == 1
    assert profiles[0]['last_name'] == "Mays"
    assert profiles[0]['score'] is None

    add_score_for_profile(profile_id=2, score=551)

    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="Philadelphia",
        state=PA,
        distance=90,
        ordering='score',
    )
    profiles = results['profiles']

    assert len(profiles) == 2
    assert profiles[0]['last_name'] == "Lidge" and profiles[0]['score'] == 551
    assert profiles[1]['last_name'] == "Balboa" and profiles[1]['score'] is None

    add_score_for_profile(profile_id=1, score=400)

    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="Philadelphia",
        state=PA,
        distance=90,
        ordering='score',
    )
    profiles = results['profiles']

    assert len(profiles) == 2
    assert profiles[0]['last_name'] == "Lidge" and profiles[0]['score'] == 551
    assert profiles[1]['last_name'] == "Balboa" and profiles[1]['score'] == 400

    # Lastly, test the search with a nonexistent city.
    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="this city does not exist",
        state=PA,
        distance=50,
    )
    assert results == {"error": "no location info for that city"}

    # test state filter
    results = find_fresh_profiles_for_criteria(
        job_id=1,
        city="Philadelphia",
        state=PA,
        distance=90,
        ordering='score',
        state_filter=PA.id,
    )
    profiles = results['profiles']

    assert len(profiles) == 1
    assert profiles[0]['last_name'] == "Balboa" and profiles[0]['score'] == 400

    cache.clear()


def add_score_for_profile(profile_id, score):
    Score(profile_id=profile_id,
          job_id=1,
          score_value=score).save()


def find_fresh_profiles_for_criteria(*args, **kwargs):
    cache.clear()
    refresh_view()
    return find_profiles_for_criteria(*args, **kwargs)


@pytest.mark.django_db
def test_distance_between_cities():
    insert_real_distance_records()

    PA = LookupState.objects.get(state_code="PA")
    NY = LookupState.objects.get(state_code="NY")

    dist_philly_nyc = distance_between_cities("Philadelphia", PA, "New York", NY)
    assert 80 < dist_philly_nyc < 81

    assert abs(distance_between_cities("Philadelphia", PA, "Philadelphia", PA)) < 0.001


def insert_real_distance_records():
    LookupCountry(id=231, country_code="US").save()

    LookupState(id=3963, country_id=231, state_code="PA").save()
    LookupState(id=3956, country_id=231, state_code="NY").save()

    LookupPhysicalLocation(id=113286,
                           city="Philadelphia",
                           state_id=3963,
                           latitude=39.9522222,
                           longitude=-75.1641667).save()
    LookupPhysicalLocation(id=91778,
                           city="New York",
                           state_id=3956,
                           latitude=40.7141667,
                           longitude=-74.0063889).save()


@pytest.mark.django_db
def test_new_page_sizes():
    insert_real_distance_records()
    create_search_view()
    PA = LookupState.objects.get(state_code="PA")

    job = Job("job name")
    job.save()

    for i in range(90):
        profile = Profile(job=job,
                          first_name="{}".format(i),
                          last_name="_",
                          city="Philadelphia",
                          state=PA)
        profile.save()

        Score(job=job,
              profile=profile,
              score_value=700-i).save()

    for page_number in (0, 1, 2, 3, 4):
        search = find_fresh_profiles_for_criteria(
            job_id=job.id,
            city="Philadelphia",
            state=PA,
            distance=100,
            ordering='score',
            page_number=page_number,
            page_size=20,
        )

        profiles = search['profiles']
        assert len(profiles) == 10 if page_number == 4 else 20
        assert first_names_of_profiles(profiles) == \
                    [str(i) for i in range(20*page_number, 20*page_number+20) if i < 90]

    for page_number in (0, 1):
        search = find_fresh_profiles_for_criteria(
            job_id=job.id,
            city="Philadelphia",
            state=PA,
            distance=100,
            ordering='score',
            page_number=page_number,
            page_size=50,
        )

        profiles = search['profiles']
        assert len(profiles) == 40 if page_number == 1 else 50
        assert first_names_of_profiles(profiles) == \
               [str(i) for i in range(50 * page_number, 50 * page_number + 50) if i < 90]

    for page_number in (0, 1, 2, 3, 4):
        search = find_profiles_for_criteria(
            job_id=job.id,
            city="Philadelphia",
            state=PA,
            distance=100,
            ordering='score',
            page_number=page_number,
            page_size=20,
        )

        profiles = search['profiles']
        assert len(profiles) == 10 if page_number == 4 else 20
        assert first_names_of_profiles(profiles) == \
               [str(i) for i in range(20 * page_number, 20 * page_number + 20) if i < 90]

    for page_number in (0, 1):
        search = find_profiles_for_criteria(
            job_id=job.id,
            city="Philadelphia",
            state=PA,
            distance=100,
            ordering='score',
            page_number=page_number,
            page_size=50,
        )

        profiles = search['profiles']
        assert len(profiles) == 40 if page_number == 1 else 50
        assert first_names_of_profiles(profiles) == \
               [str(i) for i in range(50 * page_number, 50 * page_number + 50) if i < 90]


def first_names_of_profiles(profiles):
    return [profile['first_name'] for profile in profiles]
