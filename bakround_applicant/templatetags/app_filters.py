from django import template
from datetime import datetime, date, timedelta, timezone
from dateutil import relativedelta
from django.utils.safestring import mark_safe
import json
import calendar
from bakround_applicant.all_models.db import EmployerJob, IcimsJobData
from bakround_applicant.usage.utils import get_subscription_plan_for_user, get_trial_days_remaining, get_plan_by_id
from django.shortcuts import render
import django.utils
from bakround_applicant.utilities.helpers.formatting import format_phone_number

register = template.Library()

@register.filter(name='phone_number')
def phone_number(value):
    try:
        return format_phone_number(value)
    except:
        return None

@register.filter(name='format_skill_months')
def format_skill_months(value):
    try:
        if int(value) == 12:
            return str(int(value/12)) + ' year'
        if int(value) > 12:
            return str(int(value/12)) + ' years'
        elif int(value) == 1:
            return str(int(value)) + ' month'
        elif int(value) < 12:
            return str(int(value)) + ' months'
    except (ValueError, TypeError, AttributeError):
        return None


@register.filter(name='convert_months_to_years')
def convert_months_to_years(value):
    try:
        return ('%f' % (int(value) / 12)).rstrip('0').rstrip('.')
    except (ValueError, TypeError, AttributeError):
        return None


@register.assignment_tag
def convert_state_id_to_code(states, state_id):
    try:
        return states.filter(id=state_id).first().state_code
    except (ValueError, TypeError, AttributeError):
        return None


@register.filter(name='convert_bscore_to_image_src')
def convert_bscore_to_image_src(bscore_value):
    try:
        if bscore_value > 740:
            return 'bscore_excellent.png'
        elif bscore_value > 630:
            return 'bscore_good.png'
        elif bscore_value > 520:
            return 'bscore_fair.png'
        elif bscore_value > 410:
            return 'bscore_poor.png'
        else:
            return 'bscore_verypoor.png'

    except (ValueError, TypeError, AttributeError):
        return None


@register.filter(name='convert_bscore_to_hex_color')
def convert_bscore_to_hex_color(bscore_value):
    try:
        if bscore_value > 740:
            return '#2020d0'
        elif bscore_value > 630:
            return '#8ad2e6'
        elif bscore_value > 520:
            return '#00e000'
        elif bscore_value > 410:
            return '#ff9e16'
        else:
            return '#e63c2f'
    except (ValueError, TypeError, AttributeError):
        return None

@register.assignment_tag
def round_months(months):
    try:
        return round(months/12) * 12
    except (ValueError, TypeError, AttributeError):
        return None

@register.assignment_tag
def map_degree_field(collection, id_field, custom_field, field_to_return):
    try:
        if id_field:
            for item in json.loads(collection):
                if item.get('id') == int(id_field):
                    return item.get(field_to_return)
        else:
            return custom_field
    except (ValueError, TypeError, AttributeError):
        return None

@register.assignment_tag
def get_experience_duration(present_experience, end_date, start_date):
    if present_experience:
        r = relativedelta.relativedelta(datetime.now(timezone.utc), start_date)
    else:
        r = relativedelta.relativedelta(end_date, start_date)
    output_string = ''
    if r.years != 0 or r.months != 0:
        output_string = ' ('
        if r.years:
            if r.years == 1:
                output_string += str(r.years) + ' year '
            else:
                output_string += str(r.years) + ' years '
        if r.months:
            if r.months == 1:
                output_string += str(r.months) + ' month '
            else:
                output_string += str(r.months) + ' months '
        return output_string.rstrip() + ')'


@register.filter(name='convert_bscore_to_top_x_percent')
def convert_bscore_to_top_x_percent(bscore_value):
    try:
        if bscore_value > 700:
            return 10
        elif bscore_value > 650:
            return 20
        elif bscore_value > 600:
            return 30
        elif bscore_value > 550:
            return 40
        elif bscore_value > 500:
            return 50
        elif bscore_value > 400:
            return 70
        else:
            return 90
    except (ValueError, TypeError, AttributeError):
        return 50

@register.filter(name='json_str')
def json_str(val):
    out = json.dumps(val)
    return mark_safe(out)


@register.filter
def show_date_as_month_and_year(dt):
    if dt is None:
        return None
    else:
        return calendar.month_name[dt.month] + " " + str(dt.year)


@register.filter(name='get_item')
def get_item(dictionary, key, default_value=None):
    if key in dictionary:
        return dictionary.get(key)

    return default_value


@register.filter()
def reformat_job_description(job_desc):
    if not job_desc:
        return job_desc

    job_desc = job_desc.replace("\n", " ").replace("\r", " ")

    break_before = ["\u2022"]

    for s in break_before:
        job_desc = job_desc.replace(s, "\n" + s)

    return job_desc


@register.filter()#inclusion_tag('account/subscription_panel.html')
def get_subscription_panel(user):
    if user.is_staff:
        return ''

    trial_html = ''
    plan_id = get_subscription_plan_for_user(user)
    plan_name = get_plan_by_id(plan_id)

    if plan_id is None:
        trial_days = get_trial_days_remaining(user)
        trial_html = "<span style='color: black; padding: 0px 10px 0px 5px'>(%s days remaining)</span>" % (trial_days if trial_days > -1 else 0)

    if plan_id == 'bestfit-enterprise':
        return ""
    else:

        upgrade_html = "<span><a href='/upgrade' style='color: #337ab7 !important;'>Upgrade Now</a></span>"\
                            if plan_id is None or plan_id != 'bestfit-enterprise'\
                            else ''

        html = "<span style='color: black; padding-right: 15px;'><span>" \
               "Plan: <span style='font-weight: bold'>%s</span>" \
               "</span>%s &nbsp; %s</span>" % (plan_name if plan_name is not None else 'Best Fit Trial', trial_html, upgrade_html)
        return mark_safe(html)
    # show_trial_message = False
    # trial_days_remaining = 0
    # plan = get_subscription_plan_for_user(user)
    #
    # if plan is None:
    #     show_trial_message = True
    #     trial_days_remaining = get_trial_days_remaining(user)
    #
    # return { "plan_name": plan if plan is not None else "Best Fit Trial",
    #             "trial_days_remaining": trial_days_remaining,
    #             "show_trial_message": show_trial_message
    #         }


@register.filter(name="subject")
def transform_string_for_email_subject(s):
    if s is None:
        return None
    else:
        return mark_safe(str(s).replace("\n", " "))


def get_nav_array(path):
    current_item = None
    nav_array = []

    if 'icims' in path:
        employer_nav_mapping = [
            {'id': 0, 'name': 'jobs', 'path': '/icims/jobs', 'title': 'My Jobs', 'show_for': [0,1,2,3,4,5]},
            {'id': 1, 'name': 'job_detail', 'path': '/icims/job/', 'title': 'Candidates', 'show_for': [1,2,3]},
            {'id': 2, 'name': 'job_settings', 'path': '/icims/job_settings/', 'title': 'Settings', 'show_for': [1,2,3]},
            {'id': 3,  'name': 'search', 'path': '/icims/search/', 'title': 'Search', 'show_for': [1,2,3]},
            {'id': 4,  'name': 'add_job', 'path': '/icims/add_job', 'title': 'Add a New Job', 'show_for': [0,5]},
            {'id': 5,  'name': 'candidate_status', 'path': '/icims/candidate_status_detail', 'title': 'Candidate Status', 'show_for': []}
        ]
    else:
        employer_nav_mapping = [
            {'id': 0, 'name': 'jobs', 'path': '/employer/jobs', 'title': 'My Jobs', 'show_for': [0,1,2,3,4,5]},
            {'id': 1, 'name': 'job_detail', 'path': '/employer/job/', 'title': 'Candidates', 'show_for': [1,2,3]},
            {'id': 2, 'name': 'job_settings', 'path': '/employer/job_settings/', 'title': 'Settings', 'show_for': [1,2,3]},
            {'id': 3,  'name': 'search', 'path': '/employer/search/', 'title': 'Search', 'show_for': [1,2,3]},
            {'id': 4,  'name': 'add_job', 'path': '/employer/add_job', 'title': 'Add a New Job', 'show_for': [0,5]},
            {'id': 5,  'name': 'candidate_status', 'path': '/employer/candidate_status_detail', 'title': 'Candidate Status', 'show_for': []}
        ]

    for item in employer_nav_mapping:
        if item['path'] in path:
            current_item = item
            break

    if current_item is None:
        return None, []

    for item in employer_nav_mapping:
        if current_item['id'] in item['show_for']:
            nav_array.append(item)

    return current_item, nav_array


@register.filter()
def get_employer_navigation(request):
    if isinstance(request, str):
        return ""

    html = ""

    path = None
    if isinstance(request, str):
        path = request
    else:
        path = request.path

    current_nav_item, nav_array = get_nav_array(path)

    job = None
    job_id = path.split('/')[-1] if current_nav_item is not None and current_nav_item['id'] in [1,2,3] else None
    if job_id is not None:
        if 'icims' in path:
            job = IcimsJobData.objects.get(pk=job_id)
        else:
            job = EmployerJob.objects.get(pk=job_id)

    for item in nav_array:
        if item['path'].strip()[-1] == '/':
            item['path'] = item['path'] + job_id

        job_link = ''
        span_class = 'main-link'
        if item['name'] == 'jobs' and job is not None:
            if 'icims' in path:
                job_link = '&nbsp;&nbsp;&nbsp;<i class="fa fa-arrow-right"></i>&nbsp;&nbsp;&nbsp;<a href="/icims/job/' + str(job.id) + '" style="margin-right: 10px;">' + job.job_title + '</a>'
            else:
                job_link = '&nbsp;&nbsp;&nbsp;<i class="fa fa-arrow-right"></i>&nbsp;&nbsp;&nbsp;<a href="/employer/job/' + str(job.id) + '" style="margin-right: 10px;">' + job.job_name + '</a>'
        elif item['name'] in ['job_detail', 'job_settings', 'search']:
            span_class = 'secondary-link'
        html += '<span class="' + span_class +'"><a href="' + item['path'] + '">' + item['title'] + '</a>' + job_link + '</span>'

    return mark_safe(html)


@register.filter(name="str")
def apply_str_to_value(value):
    return str(value)


@register.filter(name="as_days_ago")
def as_days_ago(datetime):
    if datetime is None:
        return ""

    days = (django.utils.timezone.now() - datetime).total_seconds() / (60 * 60 * 24)

    if days >= 2:
        return "{} days ago".format(int(days))
    elif days >= 1:
        return "1 day ago"
    else:
        return "within the last 24 hours"
