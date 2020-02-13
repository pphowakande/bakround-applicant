__author__ = "tplick"
import random

from bakround_applicant.all_models.db import Profile, Job, ProfileResume, \
                                             LookupPhysicalLocation, User, \
                                             SME, SMEFeedback, EmployerCandidateFeedback
from django.db.models import F, Count
from ..profile.profile_search import filter_profiles_by_distance
from django.db.models import Q, OuterRef, Subquery, Exists
from django.db.models.expressions import RawSQL

from collections import defaultdict, OrderedDict
from django.utils import timezone as dj_timezone
from datetime import datetime, timezone, timedelta
import calendar

# 31 March 2017: removed restriction that an SME cannot review the same resume twice

# For the given SME, we want to return a randomly chosen resume that is not
# "defective," as explained below. 90% of the time, we also require that
# the resume has already been reviewed. If no such resume exists, return None.
# The probability is given as a parameter so we can test this function with and without
# this behavior.
def choose_random_unreviewed_resume_for_sme(sme,
                                            probability_of_choosing_already_reviewed_resume=None):
    if probability_of_choosing_already_reviewed_resume is None:
        probability_of_choosing_already_reviewed_resume = rereview_probability_for_job(sme.job)

    # If an SME classifies a resume as defective in some way, we prevent the resume
    #     from being chosen anymore. A resume is defective if at least one of
    #     these conditions holds:
    #        (1) an SME has marked it as wrong_job
    #        (2) an SME has marked it as wrong_language
    #        (3) an SME has marked it as incomplete
    #
    # Also, we prevent reviews on resumes that have been reviewed by 3 different SME's.

    eligible_resumes = (ProfileResume.objects.annotate(matches_sme=Exists(
        ProfileJobMapping.objects.filter(job_id=sme.job_id, profile_id=OuterRef("profile_id"))))
                                             .exclude(matches_sme=False)
                                             .exclude(smefeedback__wrong_job=True)
                                             .exclude(smefeedback__wrong_language=True)
                                             .exclude(smefeedback__incomplete=True)
                                             .exclude(smefeedback__sme_id=sme.id)
                                             .annotate(reviewers=Count('smefeedback__sme_id', distinct=True))
                                             .exclude(reviewers__gte=3)
                                             .order_by('id'))

    eligible_resumes_in_region = filter_resumes_by_region(eligible_resumes, sme.region)

    # Some of the time, we try to choose a resume that has already been reviewed by
    #   some SME.  The frequency is controlled by the parameter
    #   probability_of_choosing_already_reviewed_resume.
    if random.random() < probability_of_choosing_already_reviewed_resume:
        eligible_resumes_in_region_already_reviewed_by_some_sme = \
                eligible_resumes_in_region.filter(id__in=SMEFeedback.objects.values('profile_resume_id'))

        choice = eligible_resumes_in_region_already_reviewed_by_some_sme.order_by("?").first()
        if choice:
            return choice

    choice = eligible_resumes_in_region.order_by("?").first()
    if choice:
        return choice

    if sme.region:
        choice = eligible_resumes.order_by("?").first()
        if choice:
            return choice

    return None

# changed on 4 October 2017
def rereview_probability_for_job(job):
    total_review_count = SMEFeedback.objects.filter(sme__job=job).count()
    unique_resume_review_count = (SMEFeedback.objects
                                             .filter(sme__job=job)
                                             .values("profile_resume_id")
                                             .distinct()
                                             .count())

    ### begin Kasey's code
    #
    #
    if unique_resume_review_count >= 1200:
        # Case 1: Job has 1200 or more resumes with reviews, then
        # increase number of reviews on what we already have.
        prob = 0.5
    elif unique_resume_review_count < 600:
        # Case 2: Job has few resumes reviewed, keep reviewing new resumes
        # to increase the reviewed resume population before focusing on re-review.
        prob = 0.01
    else:
        if float(total_review_count) / (unique_resume_review_count) < 2:
            # Case 3: Job has decent volume of reviews, need to get more reviews per resume.
            prob = 0.60
        else:
            # Case 4: Job has 3 or more reviews per resume on average, so review more new resumes
            prob = 0.01
    #
    #
    ### end Kasey's code

    return prob

def filter_resumes_by_region(resumes, region):
    if region:
        center = LookupPhysicalLocation.objects.get(city=region.city, state=region.state)
        radius = (region.radius if region.radius is not None else 100)

        locations_in_region = (filter_profiles_by_distance(LookupPhysicalLocation.objects.all(),
                                                           (center.latitude, center.longitude),
                                                           radius)
                               .values('city', 'state_id'))

        return resumes.extra(
            where = [
                "(profile.city, profile.state_id) in ({})".format(locations_in_region.query)
            ]
        )
    return resumes

def profiles_reviewed_by_sme(sme):
    return (SMEFeedback.objects
                       .filter(sme=sme)
                       .values('profile_resume__profile')
                       .distinct())

def get_resume_reviews_for_sme_by_month(guid):
    sme_with_guid = SME.objects.get(guid=guid)
    smes = (SME.objects
               .filter(email=sme_with_guid.email)
               .order_by('id'))

    qa_users = User.objects.filter(email=sme_with_guid.email)
    qa_jobs = (EmployerCandidateFeedback.objects
                                        .filter(employer_user__user__in=qa_users)
                                        .annotate(job_id=F("employer_job__job_id"))
                                        .order_by('job_id')
                                        .values('job_id')
                                        .distinct())

    sme_tallies = OrderedDict()
    for sme in smes:
        sme_tallies[sme.id] = []

    qa_tallies = OrderedDict()
    for qa_job in qa_jobs:
        qa_tallies[qa_job["job_id"]] = []

    now = dj_timezone.now()
    start_date = date_months_before(first_day_of_month(now), 5)
    full_date_range = (start_date, now)

    # SMEFeedback records
    sme_feedback_counts = (SMEFeedback.objects
                                      .filter(sme__in=smes,
                                              date_created__range=full_date_range)
                                      .annotate(month=RawSQL("EXTRACT(month FROM sme_feedback.date_created)", []))
                                      .values('sme_id', 'month')
                                      .annotate(number_of_reviews=Count('id')))

    # EmployerCandidateFeedback records
    qa_feedback_counts = (EmployerCandidateFeedback.objects
                                      .filter(employer_user__user__in=qa_users,
                                              date_created__range=full_date_range)
                                      .annotate(job_id=F("employer_job__job_id"),
                                                month=RawSQL("EXTRACT(month FROM employer_candidate_feedback.date_created)", []))
                                      .values('job_id', 'month')
                                      .annotate(number_of_reviews=Count('id')))

    months = [(i-1) % 12 + 1 for i in range(now.month-5, now.month+1)]
    sme_tallies_by_month = defaultdict(int)
    qa_tallies_by_month = defaultdict(int)

    for record in sme_feedback_counts:
        month, sme_id = record['month'], record['sme_id']
        number_of_reviews = record['number_of_reviews']
        sme_tallies_by_month[month, sme_id] = number_of_reviews

    for record in qa_feedback_counts:
        month, job_id = record['month'], record['job_id']
        number_of_reviews = record['number_of_reviews']
        qa_tallies_by_month[month, job_id] = number_of_reviews

    for month in months:
        for sme_id in sme_tallies:
            sme_tallies[sme_id].append(sme_tallies_by_month[month, sme_id])

        for job_id in qa_tallies:
            qa_tallies[job_id].append(qa_tallies_by_month[month, job_id])

    month_names = [short_name_of_month(month) for month in months]
    month_names[-1] += "\n(current)"

    return sme_tallies, qa_tallies, month_names

def first_day_of_month(date):
    return datetime(month=date.month, day=1, year=date.year, tzinfo=timezone.utc)

def date_months_before(date, number):
    month, year = date.month - number, date.year
    if month <= 0:
        month += 12
        year -= 1

    return datetime(month=month, day=date.day, year=year, tzinfo=timezone.utc)

def short_name_of_month(month):
    return calendar.month_name[month][:3]

