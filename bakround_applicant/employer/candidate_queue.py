
__author__ = "tplick"

from ..profile.profile_search import make_queryset_of_search_profiles, get_location_for_city
from ..all_models.db import LookupState, EmployerCandidateQueue, EmployerSavedSearch, \
                            Profile, EmployerJob, Employer, EmployerCandidate, \
                            EmployerSearchResult, EmployerRestrictedProfile, EmployerJobUser
from ..utilities.functions import take_n_at_a_time

from django.utils import timezone
from datetime import timedelta

import uuid

from bakround_applicant.notifications import emails
from ..services.notificationservice.util import send_email_to_candidate

from bakround_applicant.utilities.logger import LoggerFactory
logger = LoggerFactory.create('CANDIDATE_QUEUE')

from django.db import transaction


def get_search_profiles_to_insert_into_queue(employer_job, saved_search, profile_update_cutoff_date):
    params = saved_search.search_parameters

    location = get_location_for_city(employer_job.city, employer_job.state)

    minimum_score = params.get('score')
    if minimum_score is None or minimum_score < 550:
        minimum_score = 550

    search_profile_queryset = make_queryset_of_search_profiles(
        job_id=employer_job.job_id,
        location=location,
        distance=params['distance'],
        state_filter=params.get('state_filter'),
        profile_ids_to_exclude=None,
        skill_ids=params.get('skill_ids') or [],
        cert_ids=params.get('cert_ids') or [],
        min_education=params.get('min_education'),
        ordering=params.get('ordering') or 'score',
        experience=params.get('experience'),
        score=minimum_score,
    )

    candidates_in_queue = (EmployerCandidateQueue.objects
                                                 .filter(employer_job=employer_job,
                                                         dismissed=False)
                                                 .values("profile_id"))

    recently_updated_profiles = (Profile.objects
                                        .filter(last_updated_date__gte=profile_update_cutoff_date)
                                        .values("id"))

    existing_job_candidates = (EmployerCandidate.objects
                                                .filter(employer_job=employer_job)
                                                .values("profile_id"))

    already_viewed_profiles = (EmployerSearchResult.objects
                                                   .filter(employer_saved_search__employer_job=employer_job,
                                                           opened=True)
                                                   .values("profile_id"))

    restricted_profiles = (EmployerRestrictedProfile.objects
                                                    .filter(employer=employer_job.employer)
                                                    .values("profile_id"))

    return (search_profile_queryset
                    .exclude(id__in=existing_job_candidates)
                    .exclude(id__in=candidates_in_queue)
                    .exclude(id__in=already_viewed_profiles.exclude(profile_id__in=recently_updated_profiles))
                    .exclude(id__in=restricted_profiles)
                    [:25])


def insert_profiles_for_job_into_queue(employer_job, profile_update_cutoff_date):
    saved_search = (EmployerSavedSearch.objects
                                       .filter(employer_job=employer_job)
                                       .order_by('id')
                                       .last())

    if saved_search is None:
        return

    if saved_search.employer_user.is_bakround_employee:
        # If the last saved search was done by a Bakround employee,
        #   get the last non-Bakround employee's saved search and use that user
        previous_saved_search = (EmployerSavedSearch.objects
                                                   .filter(employer_job=employer_job,
                                                           employer_user__is_bakround_employee=False)
                                                   .order_by('id')
                                                   .last())
        if previous_saved_search is None:
            # If a non-Bakround employee hasn't performed a search,
            #   just use the first non-Bakround employee from the employer_user table

            employer_job_user = (EmployerJobUser.objects
                                    .filter(employer_job=employer_job,
                                            employer_user__is_bakround_employee=False)
                                    .order_by('id')
                                    .first())

            # If there is no non-Bakround employee attached to the job, use the first
            #   Bakround employee.

            if employer_job_user is None:
                employer_job_user = (EmployerJobUser.objects
                                        .filter(employer_job=employer_job)
                                        .order_by('id')
                                        .first())

            if employer_job_user is None:
                return

            employer_user_id = employer_job_user.employer_user_id
        else:
            employer_user_id = previous_saved_search.employer_user_id
    else:
        employer_user_id = saved_search.employer_user_id


    search_profiles = get_search_profiles_to_insert_into_queue(employer_job,
                                                               saved_search,
                                                               profile_update_cutoff_date)

    logger.info('query is {}'.format(search_profiles.query))

    for search_profile_batch in take_n_at_a_time(100, search_profiles.iterator()):
        records = []

        for search_profile in search_profile_batch:
            record = EmployerCandidateQueue(employer_job=employer_job,
                                            profile_id=search_profile.id,
                                            employer_saved_search=saved_search,
                                            employer_user_id=employer_user_id)
            records.append(record)

        EmployerCandidateQueue.objects.bulk_create(records)


def add_candidates_to_queue_for_employer(employer, profile_update_cutoff_date):
    for employer_job in EmployerJob.objects.filter(employer=employer, candidate_queue_enabled=True):
        try:
            logger.info('adding to queue for employer job {}'.format(employer_job.id))
            insert_profiles_for_job_into_queue(employer_job, profile_update_cutoff_date)
        except Exception as e:
            logger.error(e)


def add_candidates_to_queue():
    profile_update_cutoff_date = timezone.now() - timedelta(hours=24)

    for employer in Employer.objects.filter(candidate_queue_enabled=True):
        add_candidates_to_queue_for_employer(employer, profile_update_cutoff_date)


def get_candidates_to_contact_for_job(employer_job):
    queue_records = (EmployerCandidateQueue.objects
                                           .filter(employer_job=employer_job,
                                                   dismissed=False))

    candidates_already_contacted_for_this_job = (
                EmployerCandidate.objects
                                 .filter(employer_job=employer_job)
                                 .values("profile"))

    contact_cutoff_date = timezone.now() - timedelta(days=14)
    recently_contacted_candidates = (EmployerCandidate.objects
                                                      .filter(contacted_date__gte=contact_cutoff_date))
    candidates_who_have_responded = (EmployerCandidate.objects
                                                      .filter(responded=True)
                                                      .values("profile"))
    recently_contacted_candidates_to_ignore = (
                recently_contacted_candidates.exclude(profile__in=candidates_who_have_responded)
                                             .values("profile"))

    queryset = (queue_records.exclude(profile__in=recently_contacted_candidates_to_ignore)
                             .exclude(profile__in=candidates_already_contacted_for_this_job))

    # tplick, 5 December 2017: only contact a candidate if its employer_user has auto-contact enabled
    queryset = queryset.filter(employer_user_id__isnull=False, employer_user__auto_contact_enabled=True)

    result = queryset.order_by('id')[:25]
    # print(result.query)
    return result


def contact_queued_candidates_for_employer(employer, send_email):
    for employer_job in employer.employerjob_set.filter(open=True, auto_contact_enabled=True):
        queue_records = get_candidates_to_contact_for_job(employer_job)
        for queue_record in queue_records:
            contact_candidate_in_queue_record(queue_record, send_email)


def contact_candidate_in_queue_record(queue_record, send_email):
    employer_user_id = queue_record.employer_user_id
    if employer_user_id is None:
        employer_user_id = queue_record.employer_saved_search.employer_user_id

    candidate_record = EmployerCandidate(profile=queue_record.profile,
                                         employer_job=queue_record.employer_job,
                                         guid=str(uuid.uuid4()),
                                         employer_candidate_queue=queue_record,
                                         contacted=True,
                                         contacted_date=timezone.now(),
                                         employer_user_id=employer_user_id)
    candidate_record.save()

    if send_email:
        emails.ContactCandidate().send(employer_candidate=candidate_record)


def auto_contact_candidates(send_email=True):
    for employer in Employer.objects.filter(auto_contact_enabled=True):
        contact_queued_candidates_for_employer(employer, send_email)


def remove_old_records_from_queues():
    # Find which jobs are present in the queue.
    employer_jobs = EmployerJob.objects.filter(id__in=EmployerCandidateQueue.objects
                                                                            .values("employer_job")
                                                                            .distinct())

    for employer_job in employer_jobs:
        remove_old_records_from_queue_for_employer_job(employer_job)


def remove_old_records_from_queue_for_employer_job(employer_job):
    records_for_employer_job = EmployerCandidateQueue.objects.filter(employer_job=employer_job)
    record_count = records_for_employer_job.count()

    excess_record_count = max(0, record_count-1000)
    if excess_record_count > 100:
        excess_record_count = 100

    if excess_record_count > 0:
        # Delete up to excess_record_count records, favoring the older records.
        # But only delete the records that have been added as EmployerCandidates.

        candidates_for_job = EmployerCandidate.objects.filter(employer_job=employer_job)
        records_to_delete = (records_for_employer_job.filter(profile__in=candidates_for_job.values('profile'))
                                                     .order_by('id')
                                                     [:excess_record_count])

        logger.info('trying to delete oldest {} queue records for employer_job {}; will delete {}'.format(
                            excess_record_count, employer_job.id, records_to_delete.count()))

        records_to_delete = list(records_to_delete)
        with transaction.atomic():
            for record in records_to_delete:
                (EmployerCandidate.objects
                                  .filter(employer_candidate_queue=record)
                                  .update(employer_candidate_queue=None))
                record.delete()
