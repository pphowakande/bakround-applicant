__author__ = "natesymer"

from django.db.models import Q, F

from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile
from bakround_applicant.all_models.db import Profile, ProfilePhoneNumber, ProfileEmail, \
                                             EmployerJob, ProfileJobMapping, Score
from bakround_applicant.utilities.helpers.formatting import format_phone_number
from .profile_search import make_initials_for_profile_id
from bakround_applicant.ranking.models import IcimsJobData

def profile_to_json(profile_id,
                    employer_job_id=None,
                    hide_details=False,
                    hide_bscore=False,
                    hide_job=False,
                    hide_profile_id=True):

        details_visible = not hide_details

        profile = Profile.objects.get(id=profile_id)

        certification_set = (profile.profilecertification_set
                                    .extra(select={
                                        "issued_date_non_null":
                                            "COALESCE(issued_date, '1970-01-01')"
                                    }).order_by('-issued_date_non_null',
                                                'certification_name'))

        emails = []
        phones = []
        if details_visible:
            collect_contact_info_for_profile(profile)
            phones_raw = list(ProfilePhoneNumber.objects.filter(profile_id=profile_id).values_list('value', flat=True))
            phones = list(filter(bool, map(format_phone_number, phones_raw)))
            emails = list(ProfileEmail.all_sane().filter(profile_id=profile_id).values_list('value', flat=True))

        job_id = None
        job_name = None

        if details_visible and not hide_job:
            if employer_job_id:
                job = EmployerJob.objects.get(pk=employer_job_id)
                job_id = job.job_id
                job_name = job.job.job_name
            else:
                mapping = ProfileJobMapping.objects.filter(profile_id=profile_id).order_by("id").first()
                if mapping:
                    job_id = mapping.job_id
                    job_name = mapping.job.job_name

        if profile.last_updated_date:
            last_updated_date_display = profile.last_updated_date.date().strftime("%m/%d/%y")
        else:
            last_updated_date_display = None

        score = None
        if details_visible and not hide_bscore:
            score = int((Score.objects.filter(profile_id=profile_id, job_id=job_id)
                                      .order_by('-date_created')
                                      .values_list('score_value', flat=True)
                                      .first()) or 0) or None

        name = None
        if profile.name_verification_completed and (profile.first_name or profile.last_name):
            name = ' '.join(filter(bool, [profile.first_name, profile.last_name]))

        if not name:
            name = make_initials_for_profile_id(profile.id)

        return {
            "profile": profile,
            "name": name,
            "job_name": job_name,
            "emails": emails,
            "phones": phones,
            "experience_set": list((profile.profileexperience_set
                                      .order_by('-is_current_position',
                                                F('end_date').desc(nulls_first=True),
                                                F('start_date').desc(nulls_last=True))
                                      .select_related('state'))),
            "education_set": list(map(annotate_education_record,
                                 profile.profileeducation_set
                                        .order_by(F('degree_date').desc(nulls_last=True),
                                                  '-start_date')
                                        .select_related('state', 'degree_major', 'degree_type', 'degree_name'))),
            "certification_set": list(certification_set),
            "last_updated_date_display": last_updated_date_display,
            "score": score,
            "show_profile_id": details_visible and not hide_profile_id
        }



# INTERNAL HELPERS

def annotate_education_record(education):
    education.major = (education.degree_major_other or
                       getattr(education.degree_major, 'degree_major_name', None))
    education.degreetype = getattr(education.degree_type, 'degree_type_name', None)
    education.degreename = getattr(education.degree_name, 'degree_name', None) or education.degree_name_other
    return education


def profile_to_json_icims(profile_id,
                    icims_job_id=None,
                    hide_details=False,
                    hide_bscore=False,
                    hide_job=False,
                    hide_profile_id=True):

        details_visible = not hide_details

        profile = Profile.objects.get(id=profile_id)

        certification_set = (profile.profilecertification_set
                                    .extra(select={
                                        "issued_date_non_null":
                                            "COALESCE(issued_date, '1970-01-01')"
                                    }).order_by('-issued_date_non_null',
                                                'certification_name'))

        emails = []
        phones = []
        if details_visible:
            collect_contact_info_for_profile(profile)
            phones_raw = list(ProfilePhoneNumber.objects.filter(profile_id=profile_id).values_list('value', flat=True))
            phones = list(filter(bool, map(format_phone_number, phones_raw)))
            emails = list(ProfileEmail.all_sane().filter(profile_id=profile_id).values_list('value', flat=True))

        job_id = None
        job_name = None

        if details_visible and not hide_job:
            if icims_job_id:
                job = IcimsJobData.objects.get(pk=icims_job_id)
                job_id = job.id
                job_name = job.job_title
            elif icims_job_id:
                job = IcimsJobData.objects.get(pk=icims_job_id)
                job_id = job.job_id
                job_name = job.job_title
            else:
                mapping = ProfileJobMapping.objects.filter(profile_id=profile_id).order_by("id").first()
                if mapping:
                    job_id = mapping.job_id
                    job_name = mapping.job.job_name

        if profile.last_updated_date:
            last_updated_date_display = profile.last_updated_date.date().strftime("%m/%d/%y")
        else:
            last_updated_date_display = None

        score = None
        if details_visible and not hide_bscore:
            score = int((Score.objects.filter(profile_id=profile_id, job_id=job_id)
                                      .order_by('-date_created')
                                      .values_list('score_value', flat=True)
                                      .first()) or 0) or None

        name = None
        if profile.name_verification_completed and (profile.first_name or profile.last_name):
            name = ' '.join(filter(bool, [profile.first_name, profile.last_name]))

        if not name:
            name = make_initials_for_profile_id(profile.id)

        print("retuning-----------------")
        return {
            "profile": profile,
            "name": name,
            "job_name": job_name,
            "emails": emails,
            "phones": phones,
            "experience_set": list((profile.profileexperience_set
                                      .order_by('-is_current_position',
                                                F('end_date').desc(nulls_first=True),
                                                F('start_date').desc(nulls_last=True))
                                      .select_related('state'))),
            "education_set": list(map(annotate_education_record,
                                 profile.profileeducation_set
                                        .order_by(F('degree_date').desc(nulls_last=True),
                                                  '-start_date')
                                        .select_related('state', 'degree_major', 'degree_type', 'degree_name'))),
            "certification_set": list(certification_set),
            "last_updated_date_display": last_updated_date_display,
            "score": score,
            "show_profile_id": details_visible and not hide_profile_id
        }
