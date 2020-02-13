__author__ = 'ajaynayak'

from bakround_applicant.all_models.db import Employer, EmployerCandidate, EmployerCandidateStatus, \
    EmployerJob, EmployerCandidateResponse, UserEvent, EmployerUser
from django.db.models import Q, F, Max, Count
from bakround_applicant.event import EventActions
from datetime import datetime, timedelta
from django.template.loader import render_to_string


def get_employer_stats_dictionary(employer_id):

    one_week_threshold = datetime.now() - timedelta(days=7)
    user_ids = EmployerUser.objects.filter(employer_id=employer_id).values_list('user_id')

    context = {}

    context['count_jobs_created_last_week'] = EmployerJob.objects.filter(employer_id=employer_id, date_created__gte=one_week_threshold).count()
    context['count_candidates_added_last_week'] = UserEvent.objects.filter(user_id__in=user_ids, action=EventActions.employer_job_candidate_add, date_created__gte=one_week_threshold).count()
    context['count_candidates_contacted_last_week'] = UserEvent.objects.filter(user_id__in=user_ids, action=EventActions.employer_job_candidate_contact, date_created__gte=one_week_threshold).count()

    context['count_candidates_accepted_last_week'] = EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                                           date_updated__gte=one_week_threshold,
                                                                           accepted=True).count()

    context['count_candidates_declined_last_week'] = EmployerCandidate.objects.filter(employer_job__employer_id=employer_id,
                                                                           date_updated__gte=one_week_threshold,
                                                                           responded=True,
                                                                           accepted=False).count()

    job_data = []

    for job in EmployerJob.objects.filter(employer_id=employer_id, open=True):
        job_to_add = {}
        job_to_add['job_name'] = job.job_name
        job_to_add['location'] = '{}, {}'.format(job.city, job.state.state_code if job.state else '')

        job_candidates = EmployerCandidate.objects.filter(employer_job_id=job.id, visible=True)

        job_to_add['candidate_count'] = job_candidates.count()
        job_to_add['accepted_candidate_count'] = job_candidates.filter(accepted=True).count()
        job_to_add['declined_candidate_count'] = job_candidates.filter(responded=True, accepted=False).count()
        job_to_add['candidate_status_groups'] = []

        job_candidate_statuses = EmployerCandidateStatus.objects.\
            filter(employer_candidate__employer_job_id=job.id).\
            order_by('candidate_status_id', '-date_created').\
            distinct('candidate_status_id').\
            values_list('id')

        latest_candidate_statuses = EmployerCandidateStatus.objects.\
            filter(id__in=job_candidate_statuses).\
            values('candidate_status__status').\
            annotate(candidate_status_count=Count('candidate_status')).\
            order_by('-candidate_status_count')

        job_candidate_status_count = job_candidate_statuses.count()

        default_status_count = 0
        if job_to_add['candidate_count'] > job_candidate_status_count:
            default_status_count = job_to_add['candidate_count'] - job_candidate_status_count

        job_to_add['candidate_status_groups'].append({'status': 'New Candidate', 'count': default_status_count})

        for status in latest_candidate_statuses:
            if status:
                job_to_add['candidate_status_groups'].append({'status': status['candidate_status__status'],
                                                              'count': status['candidate_status_count']})

        job_data.append(job_to_add)

    context['job_data'] = job_data
    return context


def get_employer_stats_html(employer_id):
    context = get_employer_stats_dictionary(employer_id)
    return render_to_string("email/weekly_employer_stats.html", context)
