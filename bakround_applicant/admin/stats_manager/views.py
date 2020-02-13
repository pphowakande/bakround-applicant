
__author__ = "tplick"

from django.views import View
from django.shortcuts import render, redirect

from ...all_models.db import Employer, UserEvent, User, EmployerJob, EmployerCandidate, \
                             EmployerUser, NotificationRecipient, NotificationRecipientEvent, \
                             EmployerJobUser, Notification

from datetime import datetime, timedelta, date, time
from django.utils import timezone

from bakround_applicant.event import EventActions
from django.db.models import Count

from collections import defaultdict

from ...employer.utils import get_recruiters_list_for_job
from time import strftime


class IndexView(View):
    def get(self, request):
        context = {
            "employers": Employer.objects.exclude(job_family_id=2).order_by('company_name')
        }
        return render(request, "admin/stats_manager/index.html", context)


class EmployerView(View):
    def get(self, request, employer_id=None, customer_view=False):
        if customer_view:
            assert employer_id is not None
            employer_user = EmployerUser.objects.get(user=request.user)
            assert employer_user.employer_id == employer_id

        if not employer_id:
            return redirect('stats_manager:index')

        employer = Employer.objects.get(id=employer_id)

        employer_user_id = request.GET.get('employer_user_id') or None
        if employer_user_id == 0:
            employer_user_id = None

        if customer_view:
            events = None
        elif employer_user_id is not None:
            events = (UserEvent.objects
                               .filter(user__employeruser__id=employer_user_id)
                               .order_by('-date_created')
                               .prefetch_related("user")
                               [:1000])
        else:
            events = (UserEvent.objects
                           .filter(user__employeruser__employer=employer)
                           .order_by('-date_created')
                           .prefetch_related("user")
                           [:1000])

        start_date = request.GET.get('start_date', '2016-12-01')
        end_date = request.GET.get('end_date', strftime('%Y-%m-%d'))
        date_range = (datetime.strptime(start_date, '%Y-%m-%d'),
                      datetime.strptime(end_date, '%Y-%m-%d'))
        weekly_stats = get_employer_stats_dictionary_for_stats_manager(employer.id,
                                                                       date_range=date_range)
        all_time_stats = get_employer_stats_dictionary_for_stats_manager(employer.id,
                                                                         date_range='all_time')

        per_job_stats = get_employer_stats_per_job(employer.id)
        recruiters_lists_per_job = get_recruiter_lists_for_jobs_of_employer(employer)

        for employer_job in EmployerJob.objects.filter(employer=employer).select_related('state', 'state__country'):
            job = per_job_stats[employer_job.id]
            job['id'] = employer_job.id
            job['job_name'] = employer_job.job_name
            job['location'] = "{}, {}".format(employer_job.city, employer_job.state.state_code)
            job['recruiters'] = show_recruiters(recruiters_lists_per_job[employer_job.id])
            job['status'] = 'Open' if employer_job.open else 'Closed'

            country = employer_job.state.country
            if country.country_code != "US":
                job['location'] += " ({})".format(country.country_name)

        per_job_stats_as_list = sorted(per_job_stats.values(), key=lambda row:row['job_name'])

        context = {
            "employer": employer,
            "employer_user_id": employer_user_id,
            "employer_users": EmployerUser.objects
                                    .filter(employer=employer)
                                    .prefetch_related("user")
                                    .order_by('user__first_name')
                                    .all(),
            "events": events,
            "summary_stats": [weekly_stats, all_time_stats],
            "per_job_stats": per_job_stats_as_list,

            "start_date": start_date,
            "end_date": end_date,

            "customer_view": customer_view,
        }
        return render(request, "admin/stats_manager/employer_stats.html", context)


def get_recruiter_lists_for_jobs_of_employer(employer):
    query = (EmployerJobUser.objects
                            .filter(employer_job__employer=employer,
                                    employer_user__is_bakround_employee=False)
                            .select_related('employer_user__user')
                            .order_by('employer_job_id',
                                      'employer_user__user__first_name',
                                      'employer_user__user__last_name'))

    recruiters = defaultdict(list)
    for eju in query.iterator():
        recruiters[eju.employer_job_id].append(eju.employer_user)
    return recruiters


def show_recruiters(recruiters):
    return ", ".join("{} {}".format(rec.user.first_name, rec.user.last_name)
                     for rec in recruiters)


def get_employer_stats_dictionary_for_stats_manager(employer_id, date_range):
    user_ids = EmployerUser.objects.filter(employer_id=employer_id).values_list('user_id')

    midnight = time(hour=0,
                    minute=0,
                    second=0,
                    tzinfo=timezone.utc)

    if date_range == 'weekly':
        threshold = timezone.now() - timedelta(days=7)
        datetime_bounds = (threshold, timezone.now())
        time_range_display = "last 7 days"
    elif date_range == 'all_time':
        datetime_bounds = (timezone.now() - timedelta(days=36500), timezone.now())
        time_range_display = "all time"
    elif isinstance(date_range, tuple):
        start_date, end_date = date_range
        start_timestamp = datetime.combine(start_date, midnight)
        end_timestamp = datetime.combine(end_date, midnight) + timedelta(days=1) - timedelta(microseconds=1)
        datetime_bounds = (start_timestamp, end_timestamp)
        time_range_display = "{} to {}".format(pretty_format_date(datetime_bounds[0]),
                                               pretty_format_date(datetime_bounds[1]))
    else:
        raise ValueError('bad date_range given: {}'.format(date_range))

    context = {}

    context['time_range_display'] = time_range_display

    context['jobs_created'] = \
                EmployerJob.objects.filter(employer_id=employer_id,
                                           date_created__range=datetime_bounds).count()

    context['candidates_added'] = \
                EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                 date_created__range=datetime_bounds).count()

    context['candidates_contacted'] = \
                EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                 contacted_date__range=datetime_bounds).count()

    context['candidates_accepted'] = \
                EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                 accepted_date__range=datetime_bounds).count()

    context['candidates_declined'] = \
                EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                 rejected_date__range=datetime_bounds).count()


    # new (4 December 2017)
    candidates_contacted_in_time_frame = (EmployerCandidate.objects
                                                           .filter(employer_job__employer_id=employer_id,
                                                                   contacted_date__range=datetime_bounds,
                                                                   notification__isnull=False))

    context['candidates_contacted_via_bakround'] = \
        candidates_contacted_in_time_frame.filter(notification__in=notifications_sent()).count()

    context['candidates_who_opened_emails'] = \
        candidates_contacted_in_time_frame.filter(notification__in=notifications_opened()).count()

    context['candidates_who_reported_spam'] = \
        candidates_contacted_in_time_frame.filter(notification__in=notifications_reported_as_spam()).count()

    context['candidates_contacted_externally'] = \
                EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                 contacted_date__range=datetime_bounds,
                                                 contacted_externally=True).count()

    return context


def get_employer_stats_per_job(employer_id):
    stats = defaultdict(lambda: {'candidates_added': 0,
                                 'candidates_contacted': 0,
                                 'candidates_accepted': 0,
                                 'candidates_declined': 0,
                                 'candidates_contacted_via_bakround': 0,
                                 'candidates_who_opened_emails': 0,
                                 'candidates_who_reported_spam': 0,
                                 'candidates_contacted_externally': 0})

    candidates = EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                  visible=True)
    def annotate(queryset):
        return (queryset.values('employer_job_id')
                        .annotate(count_for_job=Count('employer_job_id')))

    candidates_added = annotate(candidates)
    candidates_contacted = annotate(candidates.filter(contacted=True))
    candidates_accepted = annotate(candidates.filter(accepted=True))
    candidates_declined = annotate(candidates.filter(responded=True,
                                                     accepted=False))
    candidates_contacted_externally = annotate(candidates.filter(contacted_externally=True))

    candidates = candidates.filter(notification__isnull=False)
    candidates_contacted_via_bakround = annotate(candidates.filter(notification__in=notifications_sent()))
    candidates_who_opened_emails = annotate(candidates.filter(notification__in=notifications_opened()))
    candidates_who_reported_spam = annotate(candidates.filter(notification__in=notifications_reported_as_spam()))

    for candidate_class in [('candidates_added', candidates_added),
                            ('candidates_contacted', candidates_contacted),
                            ('candidates_accepted', candidates_accepted),
                            ('candidates_declined', candidates_declined),
                            ('candidates_contacted_via_bakround', candidates_contacted_via_bakround),
                            ('candidates_who_opened_emails', candidates_who_opened_emails),
                            ('candidates_who_reported_spam', candidates_who_reported_spam),
                            ('candidates_contacted_externally', candidates_contacted_externally)]:
        key, record_set = candidate_class
        for record in record_set:
            employer_job_id, count = record['employer_job_id'], record['count_for_job']
            stats[employer_job_id][key] = count

    return stats


def notifications_sent():
    return Notification.objects.filter(sent=True)


def notifications_opened():
    return (NotificationRecipientEvent.objects
                                      .filter(action='open')
                                      .values('notification_recipient__notification'))


def notifications_reported_as_spam():
    return (NotificationRecipientEvent.objects
                                      .filter(action='spamreport')
                                      .values('notification_recipient__notification'))


def pretty_format_date(datetime_obj):
    # The call to replace() is here to handle dates like April 9, 2018, for which
    # strftime() gives us April 09, 2018.
    return datetime_obj.strftime("%B %d, %Y").replace(" 0", " ")
