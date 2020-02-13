__author__ = "tplick"

import uuid
import json
import os

from collections import defaultdict

# import weasyprint
import pdfkit

from django.http import HttpResponse
from django.shortcuts import redirect
from django.db.models import Q
from django.templatetags.static import static

from bakround_applicant.all_models.db import EmployerCandidate, EmployerJobUser, EmployerUser, \
                                             IndustryJobFamily, JobFamily, Job, Employer, EmployerJob, \
                                             LookupState

# This function takes a sequence and returns the elements in the sequence
#   grouped n at a time.
# e.g. take_n_at_a_time(3, [1, 2, 3, 4, 5, 6, 7]) yields [1, 2, 3], [4, 5, 6], [7]
def take_n_at_a_time(n, sequence):
    accumulator = []
    iterator = iter(sequence)

    for elt in iterator:
        accumulator.append(elt)
        if len(accumulator) >= n:
            yield accumulator
            accumulator = []

    if accumulator:
        yield accumulator


def json_result(f):
    def g(*args, **kwargs):
        result = f(*args, **kwargs)
        return HttpResponse(json.dumps(result, indent=2, sort_keys=True), content_type="text/json")
    g.__name__ = f.__name__  + " [json]"
    return g

def pdf_result(f):
    def g(*args, **kwargs):
        print("inside pdf result function----------")
        result = f(*args, **kwargs)
        print("result : ", result)
        options = {
            '--disable-local-file-access': '',
            '--keep-relative-links': '',
            '--quiet': ''
        }
        print("options : ", options)
        s = pdfkit.from_string(result, False, options=options)
        print("s : ", s)
        return HttpResponse(s, content_type="application/pdf")
    g.__name__ = f.__name__ + " [pdf]"
    return g

def employer_flag_required(f):
    def g(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_employer:
            return f(request, *args, **kwargs)
        else:
            return redirect('home')
    g.__name__ = f.__name__ + " [employer_flag_required]"
    return g


def get_website_root_url():
    return os.environ['WEBSITE_ROOT_URL'].rstrip('/')


def is_production():
    return 'https://my.bakround.com' in os.environ['WEBSITE_ROOT_URL']


def is_dev():
    return 'https://my-dev.bakround.com' in os.environ['WEBSITE_ROOT_URL']


def is_local():
    return not (is_production() or is_dev())


def has_candidate_accepted_request_for_job_associated_with_user(candidate_profile_id, viewer_user_id):
    employer_user_obj = EmployerUser.objects.filter(user_id=viewer_user_id).first()

    if employer_user_obj:
        employer_of_this_user = employer_user_obj.employer
        return EmployerCandidate.objects.filter(profile_id=candidate_profile_id,
                                                employer_job__employer=employer_of_this_user,
                                                responded=True,
                                                accepted=True).exists()
    else:
        return False


def redirect_for_login(view_name):
    response = redirect(view_name)
    response.set_cookie('has_this_browser_ever_logged_in', 'True')
    return response


def is_request_marked_as_having_ever_logged_in(request):
    return request.COOKIES.get('has_this_browser_ever_logged_in')


def employer_owner_required(f):
    def g(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_employer \
                    and EmployerUser.objects.get(user=request.user).is_owner:
            return f(request, *args, **kwargs)
        else:
            return redirect('home')
    g.__name__ = f.__name__ + " [employer_owner_required]"
    return g


def get_job_families_for_industry(industry, employer=None):
    ijf_records = IndustryJobFamily.objects.filter(industry=industry)

    job_families = list(JobFamily.objects
                                 .filter(id__in=ijf_records.values('job_family'))
                                 .order_by('family_name'))

    for job_family in job_families:
        job_family.jobs = []
    job_family_map = {job_family.id: job_family for job_family in job_families}

    jobs_in_all_families = (Job.objects
                              # AN - Removing custom jobs from the job family job list for now
                              .filter(Q(employer__isnull=True), #| Q(employer=employer),
                                      visible=True,
                                      job_family__in=job_families)
                              .order_by('job_name'))

    for job in jobs_in_all_families:
        job_family_map[job.job_family_id].jobs.append(job)

    return [job_family for job_family in job_families if job_family.jobs]


def get_job_families_for_employer(employer):
    return get_job_families_for_industry(employer.industry, employer)


def make_job_structure_for_dropdown(include_empty_choice, employer_id=None, include_invisible=False):
    if employer_id:
        employer = Employer.objects.get(id=employer_id)
        industry_filter = [Q(job_family__industryjobfamily__industry=employer.industry)]
    else:
        employer = None
        industry_filter = []

    if include_invisible:
        visibility_filter = []
    else:
        visibility_filter = [Q(visible=True)]

    filters = industry_filter + visibility_filter
    jobs = (Job.objects
                # AN - Removing custom jobs from the job family job list for now
                .filter(Q(employer__isnull=True), #| Q(employer=employer),
                        *filters)
                .select_related('job_family')
                .order_by('job_family_id',
                          'job_name'))

    # https://stackoverflow.com/questions/15210511/django-modelchoicefield-optgroup-tag

    families = defaultdict(list)

    for job in jobs:
        families[job.job_family.family_name].append((job.id, job.job_name))

    result = sorted(families.items())
    if include_empty_choice:
        result = [('', [('', '-' * 9)])] + result
    return result


def make_employer_job_structure_for_dropdown(include_empty_choice, employer_id=None, include_closed=False):
    if employer_id is None:
        raise Exception('must supply employer_id to make_employer_job_structure_for_dropdown')

    if include_closed:
        visibility_filter = []
    else:
        visibility_filter = [Q(open=True)]

    employer_jobs = (EmployerJob.objects
                                .filter(employer_id=employer_id,
                                        *visibility_filter)
                                .select_related('job',
                                                'job__job_family',
                                                'state')
                                .order_by('job__job_family_id',
                                          'job_name'))

    # https://stackoverflow.com/questions/15210511/django-modelchoicefield-optgroup-tag

    families = defaultdict(list)

    for employer_job in employer_jobs:
        job_string = "{} ({}, {})".format(employer_job.job_name,
                                          employer_job.city,
                                          employer_job.state.state_code)
        families[employer_job.job.job_family.family_name].append((employer_job.id, job_string))

    result = sorted(families.items())
    if include_empty_choice:
        result = [('', [('', '-' * 9)])] + result
    return result


def make_choice_set_for_state_codes(empty_choice=None):
    result = []

    if empty_choice is not None:
        result.append(('', [('', empty_choice)]))

    us_states = LookupState.objects.filter(country__country_code="US").order_by('state_code')
    us_entries = [(state.id, state.state_code) for state in us_states]
    result.append(('United States', us_entries))

    ca_states = LookupState.objects.filter(country__country_code="CA").order_by('state_code')
    ca_entries = [(state.id, state.state_code) for state in ca_states]
    result.append(('Canada', ca_entries))

    return result


def generate_unique_file_name(original_file_name=None, new_extension=None):
    new_file_name = str(uuid.uuid4()).replace('-', '')

    old_extension = None

    if original_file_name is not None and new_extension is None:
        # if the attached file has an extension, preserve it in the output filename
        original_file_parts = original_file_name.split('.')
        if len(original_file_parts) > 1:
            old_extension = original_file_parts[len(original_file_parts)-1]

    if new_extension is not None:
        new_file_name = '{}.{}'.format(new_file_name, new_extension)
    elif old_extension is not None:
        new_file_name = '{}.{}'.format(new_file_name, old_extension)

    return new_file_name
