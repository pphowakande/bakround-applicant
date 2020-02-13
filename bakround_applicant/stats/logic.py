#!/usr/bin/env python3

from django.conf import settings
from django.db import connection

from bakround_applicant.all_models.db import Job, LookupState, LookupPhysicalLocation, Profile


METRO_AREA_QUERY = """
SELECT count(*)
FROM "search_profile_view4"
WHERE ("search_profile_view4"."scored_job_id" in {jobs}
  AND (3959 * acos( cos( radians({center_latitude}) ) * cos( radians( latitude ) ) * cos( radians( longitude ) -
       radians({center_longitude}) ) + sin( radians({center_latitude}) ) * sin( radians( latitude ) ) )
       <= {distance}));
"""


METRO_AREA_EXPERIENCE_QUERY = """
SELECT count(distinct search_profile_view4.id) as count, initcap(company_name) as name
FROM "search_profile_view4" inner join profile_experience on search_profile_view4.id = profile_experience.profile_id
WHERE ("search_profile_view4"."scored_job_id" in {jobs}
  AND (3959 * acos( cos( radians({center_latitude}) ) * cos( radians( latitude ) ) * cos( radians( longitude ) -
       radians({center_longitude}) ) + sin( radians({center_latitude}) ) * sin( radians( latitude ) ) )
       <= {distance}))
  AND (company_name ilike '%Hospital%' or company_name ilike '%Health%' or company_name ilike '%Hospice%')
GROUP BY name
ORDER BY count DESC
LIMIT 10;
"""


MAJOR_CITIES = ["Philadelphia, PA",
                "New York, NY",
                "Washington, DC",
                "Boston, MA",
                "Los Angeles, CA",
                "San Diego, CA",
                "San Francisco, CA",
                "Chicago, IL",
                "Dallas, TX",
                "Houston, TX",
                "Miami, FL",
                "Atlanta, GA",
                "Denver, CO"]
assert all(len(city_string.split(", ")) == 2 for city_string in MAJOR_CITIES)


def get_database_name():
    full_name = settings.DATABASES['default']['HOST'] + "."
    return full_name[:full_name.index('.')]


def get_stats_with_cursor(cursor):
    lines = []
    print = (lambda s="": lines.append(s))

    print("Connected to database at {}.".format(get_database_name()))

    query = (lambda sql, params=(): get_first_result(cursor, sql, params))
    all_job_ids = [job.id for job in Job.objects.all()]
    home_health_job_ids = [job.id for job in Job.objects.filter(job_name__icontains='Home Health')]

    print("total number of profiles in database: {}".format(
        query("""
            select count(*)
            from profile
        """)))

    print("number of profiles with health-care experience: {}".format(
        query("""
            select count(distinct profile_id)
            from profile_experience
            where company_name ilike '%Hospital%' or company_name ilike '%Health%' or company_name ilike '%Hospice%'
        """)))

    print("number of profiles with Bayada experience: {}".format(
        query("""
            select count(distinct profile_id)
            from profile_experience
            where company_name ilike '%Bayada%'
        """)))

    home_health_profile_count = Profile.objects.filter(job_id__in=home_health_job_ids).count()
    print("number of profiles with job id set to home health: {}".format(home_health_profile_count))

    print()

    for distance in [50]:
        for (description, id_set) in [("all jobs", all_job_ids),
                                      ("home health", home_health_job_ids)]:
            if not id_set:
                continue

            for city_string in MAJOR_CITIES:
                location = get_location_for_city(city_string)

                count = fill_in_query(cursor, METRO_AREA_QUERY, location, id_set, distance)
                print("number of profiles for {} within {} miles of {}: {}".format(
                    description, distance, city_string, count
                ))

                experience_sql = METRO_AREA_EXPERIENCE_QUERY.format(center_latitude=location.latitude,
                                                                    center_longitude=location.longitude,
                                                                    distance=distance,
                                                                    jobs="(" + ",".join(str(id) for id in id_set) + ")")
                cursor.execute(experience_sql)
                print("Top 10 health-related employers for these profiles:")
                top_employers = [(count, name) for (count, name) in cursor]
                for (count, name) in top_employers:
                    print("{} ({})".format(clean_up_hospital_name(name), count))

                print()

    return '\n'.join(lines)


def clean_up_hospital_name(name):
    name = name.replace("'S", "'s")
    for word in ["Of", "And", "The"]:
        word = " " + word + " "
        name = name.replace(word, word.lower())
    return name


def fill_in_query(cursor, sql, location, ids, distance):
    return get_first_result(cursor,
                            sql.format(jobs="(" + ",".join(str(id) for id in ids) + ")",
                                       distance=distance,
                                       center_latitude=location.latitude,
                                       center_longitude=location.longitude))


def get_first_result(cursor, sql, params=()):
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    for row in cursor:
        return row[0]


def get_location_for_city(city_string):
    city, state_code = city_string.split(", ")
    state = LookupState.objects.get(state_code=state_code, country__country_code="US")
    return LookupPhysicalLocation.objects.get(city=city, state=state)


def get_stats():
    with connection.cursor() as cursor:
        return get_stats_with_cursor(cursor)
