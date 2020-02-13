
__author__ = "tplick"

from django.core.cache import cache
from ..utilities.logger import LoggerFactory
import json
from django.http import HttpResponse
from django.views.generic import View
import django.middleware.csrf
from datetime import datetime, timedelta
from ..all_models.db import Profile, ProfileExperience, EmployerJob, LookupPhysicalLocation
from django.utils import timezone
from ..profile.profile_search import get_location_for_city, distance_between_locations, distance_between_cities
import ast
from django.shortcuts import render
import time
from ..utilities.functions import take_n_at_a_time


logger = LoggerFactory.create('closeability_metric')


def fetch_closeability_metric_for_profile_ids(profile_ids, employer_job_id):
    # remove duplicates
    profile_ids = list(set(profile_ids))

    all_metrics = {}

    for batch in take_n_at_a_time(100, profile_ids):
        metrics_for_batch = fetch_closeability_metric_for_batch(batch, employer_job_id)
        all_metrics.update(metrics_for_batch)

    return all_metrics


def fetch_closeability_metric_for_batch(profile_ids, employer_job_id):
    employer_job = EmployerJob.objects.get(id=employer_job_id)
    cache_keys = {pid: "closeability_metric_{}_{}".format(pid, employer_job_id) for pid in profile_ids}
    cached = cache.get_many(cache_keys.values())
    map_of_cached_values = {pid: cached.get(cache_keys[pid]) for pid in profile_ids}

    metrics = {}
    metrics_calculated_now = {}

    profiles = {profile.id: profile
                for profile in Profile.objects.filter(id__in=profile_ids)}
    attach_experience_to_profiles(profiles)

    attach_locations_to_profiles_and_experiences(profiles.values())
    employer_job.location = get_location_for_city(employer_job.city, employer_job.state)

    for pid in profile_ids:
        if map_of_cached_values.get(pid) is not None:
            metrics[pid] = float(map_of_cached_values.get(pid))
            # logger.info('cached clos metric for profile {} is {}'.format(pid, metrics[pid]))
        else:
            metrics[pid] = metrics_calculated_now[pid] = \
                calculate_closeability_metric_for_profile_id(pid, profiles.get(pid), employer_job)
            # logger.info('calculated clos metric for profile {} as {}'.format(pid, metrics[pid]))

    if metrics_calculated_now:
        cache.set_many({"closeability_metric_{}_{}".format(pid, employer_job_id): metric
                        for (pid, metric) in metrics_calculated_now.items()},
                       3600)
    return metrics


# ranges from 0 to 10
def calculate_closeability_metric_for_profile_id(profile_id, profile, employer_job):
    try:
        if not profile.city or not profile.state_id:
            return -1.0

        profile_location = profile.location
        potential_job_location = employer_job.location
        current_job_locations = get_current_job_locations_for_profile(profile)
        current_job_location = closest_location_to(current_job_locations, profile_location)

        current_job_time = time_in_current_job(profile)
        average_job_time = average_time_in_each_job(profile)

        distance_from_current_job = distance_between_locations(profile_location, current_job_location) \
                                        if current_job_location else 0.0
        distance_from_potential_job = distance_between_locations(profile_location, potential_job_location)

        component1 = distance_from_current_job / (distance_from_current_job + distance_from_potential_job + 1.0)
        component2 = current_job_time.days / (current_job_time.days + average_job_time.days + 1.0)

        time_threshold = timezone.now() - timedelta(days=31)
        component3 = 1.0 if profile.last_updated_date is not None \
                            and profile.last_updated_date > time_threshold \
                        else 0

        return 5.0 * (component1 + component2 + component3)
    except Exception as e:
        logger.exception(e)
        return -1.0


# returns a timedelta object
def time_in_current_job(profile):
    time_in_job = timedelta(days=0)
    for exp in profile.current_experience:
        if exp.start_date:
            time_in_job += (timezone.now() - exp.start_date)
    return time_in_job


# returns a timedelta object
def average_time_in_each_job(profile):
    tenures = []
    zero_time = timedelta(days=0)

    for exp in profile.all_experience:
        if exp.start_date and exp.end_date:
            tenure = exp.end_date - exp.start_date
        elif exp.start_date:
            tenure = timezone.now() - exp.start_date
        else:
            tenure = None

        if tenure is not None:
            tenures.append(tenure)

    return (sum(tenures, zero_time) / len(tenures)) if tenures else zero_time


def get_current_job_locations_for_profile(profile):
    locations = []
    i = 0
    for exp in profile.all_experience:
        try:
            if i == 0 or exp.end_date is None:
                location = exp.location
                if not location:
                    raise Exception()
                locations.append(location)
            i += 1
        except Exception:
            pass
    return locations


def closest_location_to(locations, target):
    distances = [(distance_between_locations(loc, target), loc) for loc in locations]
    return min(distances)[1] if distances else None


class CloseabilityMetricView(View):
    def post(self, request):
        json_obj = json.loads(request.body.decode('utf8'))
        profile_ids = json_obj['profile_ids']
        employer_job_id = json_obj['employer_job_id']

        metrics = fetch_closeability_metric_for_profile_ids(profile_ids, employer_job_id)
        return HttpResponse(json.dumps(metrics),
                            content_type="application/json")

    def get(self, request):
        return HttpResponse("""
<html>
<form method="POST" id="the_form">

<input type=hidden name=json id=json_field>
Profile ids: <input type=text id="profile_ids"><br/>
Employer job id: <input type=text id="emp_job_id"><br/>
<input type=button onclick="submit_json()" value="Submit">
</form>

<br />
Output:
<br />
<span id="output"></span>
<script src="../static/vendor/jquery-3.1.1.min.js"></script>
<script>
function submit_json()
{
    var emp_job_id = document.getElementById("emp_job_id").value;
    var profile_ids = document.getElementById("profile_ids").value;

    var json_obj = {
        "profile_ids": profile_ids.split(",").map(function (elt, i){return Number(elt.trim())}),
        "employer_job_id": Number(emp_job_id)
    };

    $.ajax({
          method: "POST",
          headers: {
			'X-CSRFToken': "%s"
		  },
		  cache: false,
		  data: JSON.stringify(json_obj),
          url: "/employer/closeability_metric"
        }).done(function (response) {
          $("#output").text(JSON.stringify(response))
        });
}
</script>
        """ % (django.middleware.csrf.get_token(request)))


class CloseabilityMetricSqlView(View):
    def get(self, request):
        start_time = time.time()
        employer_job_id = int(request.GET['j'])
        profile_ids = ast.literal_eval(request.GET['p'])

        cache.clear()
        result = fetch_closeability_metric_for_profile_ids(profile_ids, employer_job_id)

        time_taken = time.time() - start_time
        message = str(result) + " (took {} seconds)".format(time_taken)
        return render(request, "pages/generic_message.html", {"message": message})


def attach_experience_to_profiles(profiles):
    for profile in profiles.values():
        profile.current_experience = []
        profile.all_experience = []

    for exp in ProfileExperience.objects.filter(profile__in=profiles).order_by('-end_date'):
        profile = profiles[exp.profile_id]
        if len(profile.all_experience) < 50:
            profile.all_experience.append(exp)
            if exp.is_current_position:
                profile.current_experience.append(exp)


def attach_locations_to_profiles_and_experiences(profiles):
    all_cities = (set((profile.city, profile.state_id) for profile in profiles) |
                  set((exp.city, exp.state_id) for profile in profiles for exp in profile.all_experience))
    non_null_cities = tuple((city, state_id) for (city, state_id) in all_cities
                                if city is not None and state_id is not None)

    location_mapping = {}
    if non_null_cities:
        # https://stackoverflow.com/a/30615496
        query = LookupPhysicalLocation.objects.raw('''
                        select *
                        from lookup_physical_location
                        where (city, state_id) in %s
                ''', [non_null_cities])

        for loc in query:
            location_mapping[loc.city, loc.state_id] = loc

    for profile in profiles:
        profile.location = location_mapping.get((profile.city, profile.state_id))
        for exp in profile.all_experience:
            exp.location = location_mapping.get((exp.city, exp.state_id))
        # We do not have to handle current_experience separately, because its objects are the same
        #    as the objects in all_experience.
