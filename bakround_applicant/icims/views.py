# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import io
from io import StringIO
import csv
import base64
import re
import os
import json
import uuid
import string
import datetime
from datetime import timedelta
from collections import defaultdict
from django.conf import settings
from django.core import serializers
from django.core.mail import EmailMessage
from django import forms
from django.forms import ModelForm, BooleanField
from django.forms.models import ModelChoiceField
from django.forms.fields import ChoiceField
from django.db.models.expressions import RawSQL
from django.db.models import Count, F, Q
from django.db.models import FileField
from django.db.models import Subquery, OuterRef, Q
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse

from lxml import objectify, etree

from ..all_models.db import Profile, ProfileResume, ProfileEducation, ProfileSkill, ProfileExperience, \
                            ProfileCertification, LookupState, LookupCountry, ProfileViewer, ProfileViewerAction, \
                            LookupDegreeType, LookupDegreeMajor, LookupDegreeName, Skill, Job, JobSkill, Certification, \
                            JobCertification, Employer, User, EmailAddress, \
                            EmployerCandidateStatus, LookupCandidateStatus, EmployerSavedSearch, EmployerSearchResult, \
                            EmployerRestrictedProfile, LookupRejectReason, EmployerCandidateFeedback, \
                            EmployerProfileView, EmployerJob, EmployerCandidate, \
                            EmployerUser, EmployerJobUser, UserEvent, ProfileEmail, ProfilePhoneNumber


from ..all_models.db import IcimsJobData, ICIMSApplicantWorkflowData

from bakround_applicant.profile.profile_search import convert_profile_to_json, make_search_profile_model, \
                                     annotate_profiles_with_distance, convert_decimal_to_float, get_location_for_city, make_queryset_of_search_profiles, convert_page_to_json, list_candidates_for_job, list_candidates_for_icims_job

from bakround_applicant.utilities.helpers.dict import get_first_matching
from bakround_applicant.utilities.functions import get_website_root_url, json_result, make_job_structure_for_dropdown, \
                                                   make_choice_set_for_state_codes, get_job_families_for_employer, json_result, employer_flag_required, \
                                                   generate_unique_file_name
from django.views.decorators.gzip import gzip_page

from bakround_applicant.forms import BakroundSignupForm, EmployerSignupForm
from bakround_applicant.event import record_event, EventActions

from bakround_applicant.forms import RestrictedFileField
from bakround_applicant.utilities.file_io import FileIO
from bakround_applicant.utilities.helpers.formatting import format_phone_number
from bakround_applicant.usage import utils
from bakround_applicant.sme_feedback.views import fill_in_checkbox_columns

from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.services.notificationservice.util import get_default_email_body, send_follow_up_emails
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact

from bakround_applicant.admin.stats_manager import views as stats_manager_views
from bakround_applicant.notifications import emails as email

from .forms import EmployerUserForm, UploadLogoForm
from .mixins import SubscriptionRequiredMixin
from .utils import add_candidate_to_job, contact_candidate, get_application_inbox, get_logo_image_html, \
                   get_jobs_for_employer_user, validate_job_location, is_employer_job_location_distinct, \
                   does_closed_job_exist_for_location, replace_tags_in_initial_custom_email, generate_custom_email_address

EMPLOYER_ASSETS_FOLDER = 'employer_assets'
EMPLOYER_LOGO_HTML_TAG = '::LOGO_HERE::'


def get_employer_user(user_id):
    return EmployerUser.objects.get(user_id=user_id)


class JobChoiceField(ModelChoiceField):
   def label_from_instance(self, obj):
        # return your own label here...
        return obj.job_name


class StateChoiceField(ModelChoiceField):
   def label_from_instance(self, obj):
        # return your own label here...
        return obj.state_code


class JobForm(ModelForm):
    job_name = forms.CharField(label='Job Name', max_length=255, required=True)
    # city = forms.CharField(label='City', max_length=128, required=True)

    job = ChoiceField([])

    state = ChoiceField([], required=True)
    open = BooleanField(required=False)

    class Meta:
        model = EmployerJob
        fields = ['id', 'city', 'custom_email_body', 'open', 'job_description']

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'job' or field_name == 'state':
                field.widget.attrs['class'] = 'browser-default'

        self.fields['state'].choices = make_choice_set_for_state_codes()

    def limit_jobs_to_employer(self, employer_id):
        self.fields['job'].choices = make_job_structure_for_dropdown(False, employer_id)


class IcimsPreviewCandidateContact(LoginRequiredMixin, View):
    def get(self, request, icims_job_id):
        profile_id = int(request.GET.get('profile_id') or 0)

        employer_user = get_employer_user(request.user.id)
        employer_job = IcimsJobData.objects.get(id=int(icims_job_id))
        profile = Profile.objects.get(id=profile_id)

        print("email : ", email)

        mock_candidate = EmployerCandidate(profile=profile, employer_job=employer_job, employer_user=employer_user)
        n = email.ContactCandidate().build(employer_candidate=mock_candidate)
        context = {
            'subject': n.subject,
            'body': n.body,
            'metadata': n.metadata
        }
        return render(request, 'employer/preview_candidate_contact.html', context)


class IcimsIndexView(LoginRequiredMixin, View):

    def get(self, request):

        return redirect("icims:jobs")

    def dispatch(self, *args, **kwargs):
        return super(IcimsIndexView, self).dispatch(*args, **kwargs)


class IcimsJobsView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def dispatch(self, *args, **kwargs):
        return super(IcimsJobsView, self).dispatch(*args, **kwargs)

    def get(self, request):
        icims_jobs = IcimsJobData.objects.filter()
        print("icims_jobs : ", icims_jobs)
        job_candidates = {}
        job_total_candidate_count = list(ICIMSApplicantWorkflowData.objects
                                   .filter()
                                   .values('job_url')
                                   .annotate(candidate_count=Count('id')))
        print("job_total_candidate_count : ", job_total_candidate_count)

        for index, item in enumerate(job_total_candidate_count):
            job_candidates[item['job_url']] = {}
            job_candidates[item['job_url']]['total_count'] = item['candidate_count']

        print("job_candidates : ", job_candidates)
        context = {
            'job_candidates': job_candidates,
            'icims_jobs': icims_jobs,
        }
        return render(request, "icims/jobs.html", context)


class IcimsJobDetailView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, icims_job_id):
        print("IcimsJobDetailView  funtion")
        print("icims_job_id : ", icims_job_id)
        job = IcimsJobData.objects.get(pk=icims_job_id)
        employer_user = get_employer_user(request.user.id)

        context = {
            'job': job,
            'application_inbox': '',
            'props': json.dumps({
                'tour_dismissed': employer_user.jobdetail_tour_dismissed,
                'icims_job_id': job.id,
                'job_profile': { 'id': job.id, 'job_name': job.job_title },
                'job_open': '',
                'city': '',
                'state': ''
            })
        }
        print("context : ", context)
        return render(request, "icims/job_detail.html", context)

class IcimsAddJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def get(self, request, previous_form=None):

        employer_user = EmployerUser.objects.get(user=request.user)
        employer = employer_user.employer

        employer_users = EmployerUser.objects.filter(employer=employer_user.employer)\
                                                            .annotate(user_first_name=F('user__first_name'))\
                                                            .annotate(user_last_name=F('user__last_name'))\
                                                            .order_by('user_first_name')

        state_lists = [
            {"country_name": "United States",
             "states": LookupState.objects.filter(country__country_code="US").order_by('state_code')},
            {"country_name": "Canada",
             "states": LookupState.objects.filter(country__country_code="CA").order_by('state_code')},
        ]

        form = JobForm()
        form.limit_jobs_to_employer(employer_user.employer_id)
        form.initial['custom_email_body'] = get_default_email_body(employer=employer_user.employer)

        logo_url = None
        logo_file_name = employer_user.employer.logo_file_name
        if logo_file_name is not None:
            logo_url = get_logo_url(logo_file_name)

        job_families = get_job_families_for_employer(employer)

        if previous_form:
            form.initial['custom_email_body'] = previous_form.cleaned_data['custom_email_body']

        low_accuracy_jobs = list(Job.objects.filter(employer_id__isnull=True, accuracy__lt=2).values_list('id', flat=True))

        context = {
            "form": form,
            "logo_html_tag": EMPLOYER_LOGO_HTML_TAG,
            "logo_url": logo_url,
            "employer_user_id": employer_user.id,
            "employer_users": employer_users,
            "state_lists": state_lists,
            "job_families": job_families,
            "low_accuracy_jobs": low_accuracy_jobs,
            "is_demo_account": employer.is_demo_account,
            "can_edit_email": request.user.is_staff or employer_user.is_bakround_employee
        }

        return render(request, "icims/add_job.html", context)

    def post(self, request):

        form = JobForm(request.POST)

        employer_user = EmployerUser.objects.get(user=request.user)
        employer_id = employer_user.employer_id
        form.limit_jobs_to_employer(employer_id)

        if form.is_valid():

            job_id = form.cleaned_data['job']

            city = string.capwords(form.cleaned_data['city'])
            if not validate_job_location(city, form.cleaned_data['state']):
                messages.error(request, 'Please enter a valid city/state combo.')
                return self.get(request, previous_form=form)

            # if not is_employer_job_location_distinct(employer_id, job_id, city, form.cleaned_data['state']):
            #     if does_closed_job_exist_for_location(employer_user.employer_id, job_id, city, form.cleaned_data['state']):
            #         messages.error(request, 'This job already exists for the city you’ve chosen, but has been closed. Please re-activate the existing job by clicking on All Jobs on the Welcome page.')
            #     else:
            #         messages.error(request, 'A job of this type already exists for the same city/state combo.')
            #     return self.get(request, previous_form=form)

            if 'notifications' not in request.POST:
                messages.error(request, 'Please select at least one user to receive notifications.')
                return self.get(request, previous_form=form)

            job = Job.objects.get(pk=job_id)

            employer_job = EmployerJob(employer_id=get_employer_user(request.user.id).employer_id,
                                       job_id=job.id,
                                       job_name=form.cleaned_data['job_name'],
                                       city=city,
                                       state_id=form.cleaned_data['state'],
                                       guid=str(uuid.uuid4())[:8],
                                       job_description=form.cleaned_data['job_description'])

            if 'custom_email_body' in form.cleaned_data:
                data = form.cleaned_data['custom_email_body']
                employer_job.custom_email_body = extract_inline_images(data) if data.strip() != '' else None

                if employer_job.custom_email_body is not None and EMPLOYER_LOGO_HTML_TAG in employer_job.custom_email_body:
                    if employer_job.employer.logo_file_name is None:
                        messages.error(request, 'Please upload a logo before inserting the logo tag.')
                        return redirect("icims:add_job")
                    employer_job.custom_email_body = employer_job.custom_email_body.replace(EMPLOYER_LOGO_HTML_TAG, get_logo_image_html(logo_url=get_logo_url(employer_job.employer.logo_file_name)))

                # replace tags like {CITY}, etc.
                employer_job.custom_email_body = replace_tags_in_initial_custom_email(employer_job.custom_email_body,
                                                                                      employer_job)


            employer_job.save()

            notification_user_ids = list(map(int, request.POST.getlist('notifications')))
            for user_id in notification_user_ids:
                try:
                    employer_user = EmployerUser.objects.get(pk=user_id)
                    employer_job_user = EmployerJobUser(icims_job_id=employer_job.id,
                                                    employer_user=employer_user,
                                                    added_by=employer_user)

                    employer_job_user.save()
                except:
                    pass

            messages.success(request, 'Job added successfully.')

            record_event(request.user,
                     EventActions.employer_job_create,
                     {"icims_job_id": employer_job.id})

            return redirect("icims:search", icims_job_id=employer_job.id)
        else:
            messages.error(request, 'Please fix the validation errors and try again.')

            return redirect("icims:add_job")


class IcimsJobCandidatesListView(LoginRequiredMixin, View):
    def go(self, request, icims_job_id, params):
        print("inside IcimsJobCandidatesListView go funtion------------ ")
        page = max(int(params.get('page', 0)), 0)
        per_page = int(params.get('per_page', 20))
        ordering = params.get('ordering', 'score')

        q = {}
        if 'contacted' in params:
            q['contacted'] = bool(params['contacted'])
        if 'responded' in params:
            q['responded'] = bool(params['responded'])
        if 'accepted' in params:
            q['accepted'] = bool(params['accepted'])

        icims_job = IcimsJobData.objects.filter(id=icims_job_id).first()

        if not icims_job:
            return {'success': False}

        fake_ecs = EmployerCandidate.objects.filter(**({**q, 'employer_job_id': icims_job_id}))
        print("fake_ecs : ", fake_ecs)
        total = fake_ecs.count()
        total_interested = fake_ecs.filter(accepted=True).count()
        print("total_interested : ", total_interested)
        print("calling function list_candidates_for_icims_job------------")
        qs = list_candidates_for_icims_job(icims_job_id, page, per_page, q, ordering)

        print("qs : ", qs)

        return { 'success': True, 'results': convert_page_to_json(page, qs, serialize=False), 'count': total, 'count_interested': total_interested }

    @json_result
    def get(self, request, icims_job_id):
        return self.go(request, icims_job_id, request.GET)

    @json_result
    def post(self, request, icims_job_id):
        params = json.loads(request.body.decode('utf8'))
        return self.go(request, icims_job_id, params)

class CandidateContactView(LoginRequiredMixin, View):
    @json_result
    def post(self, request, candidate_id):
        try:
            params = json.loads(request.body.decode('utf8'))
        except:
            params = {}
        return self.go(request, candidate_id, params)

    @json_result
    def get(self, request, candidate_id):
        return self.go(request, candidate_id, request.GET)

    def process_cms(self, lst):
        l = []
        for x in lst:
            value = x.value
            if isinstance(x, ProfilePhoneNumber):
                value = format_phone_number(value)
            if value:
                l.append({ 'value': value, 'assurance': 1 if x.is_correct_person else 2 })
        return l

    def go(self, request, candidate_id, params):
        ec = EmployerCandidate.objects.get(id=candidate_id)
        return {
            'emails': self.process_cms(ProfileEmail.all_sane().filter(profile_id=ec.profile_id)),
            # We return all the phones because we have no way of telling which ones are sane or not.
            'phones': self.process_cms(ProfilePhoneNumber.objects.filter(profile_id=ec.profile_id))
        }

def get_response_date_for_ordering_for_candidate(candidate):
    accepted_date = candidate.get("accepted_date")
    rejected_date = candidate.get("rejected_date")

    if accepted_date:
        return accepted_date.isoformat()
    elif rejected_date:
        return rejected_date.isoformat()
    else:
        return "0000"


def get_contact_date_for_ordering_for_candidate(candidate):
    date = candidate.get("contacted_date")

    if date:
        return date.isoformat()
    else:
        return "0000"

class ProfileSearchView(LoginRequiredMixin, View):
    title = 'IcimsSearchView'
    template = 'icims/search.html'

    def get(self, request, icims_job_id):
        employer_user = EmployerUser.objects.get(user=request.user)

        job = IcimsJobData.objects.get(pk=icims_job_id)
        job_profile = job

        state_list = list(LookupState.objects
                                     .filter(country__country_code="US")
                                     .order_by('state_code')
                                     .values("id", "state_name", "state_code"))

        context = {
            'title': self.title,
            'props': json.dumps({
                'state_list': state_list,
                'job_id': job.id,
                'job_profile': {'id': job_profile.id, 'job_name': job_profile.job_title},
                'city': '',
                'state': '',
                'tour_dismissed': employer_user.search_tour_dismissed,
                'show_advanced_search': False # TODO: bring this back!
            }),
            'icims_job_id': icims_job_id,
            'job': job,
            'employer': employer_user.employer
        }

        return render(request, self.template, context)

class ProfileSummaryView(View):
    def make_date_range_for_exp(self, exp, missing = "???"):
        if not exp.start_date and not exp.end_date and not exp.is_current_position:
            return None

        start = exp.start_date.strftime("%B %Y") if exp.start_date else None
        end = "Present" if exp.is_current_position else (exp.end_date.strftime("%B %Y") if exp.end_date else None)
        return "{} - {}".format(start or missing, end or missing)

    @json_result
    def get(self, request, profile_id):
        print("inside ProfileSummaryView get function--------------")
        print("profile_id : ", profile_id)
        profile_education = [{
            'school_name': pe.school_name,
            'school_type': pe.school_type,
            'degree_major': pe.degree_major.degree_major_name if pe.degree_major else pe.degree_major_other,
            'degree_name': pe.degree_name.degree_name if pe.degree_name else pe.degree_name_other,
            'degree_year': pe.degree_date.year if pe.degree_date else None
        } for pe in ProfileEducation.objects.filter(profile_id=profile_id).order_by('-degree_date')]

        print("profile_education : ", profile_education)

        profile_experience_qs = (ProfileExperience.objects
                                               .filter(profile_id=profile_id)
                                               .order_by('-is_current_position',
                                                         F('end_date').desc(nulls_first=True),
                                                            F('start_date').desc(nulls_last=True)))

        print("profile_experience_qs : ", profile_experience_qs)

        profile_experience = [{
            'date_range': self.make_date_range_for_exp(pe),
            'company_name': pe.company_name,
            'position_title': pe.position_title
        } for pe in profile_experience_qs]

        print("profile_experience : ", profile_experience)

        profile_skills = [{
            'name': skill.skill.skill_name,
            'experience_months': skill.experience_months,
        } for skill in ProfileSkill.objects.filter(profile_id=profile_id).order_by('-last_used_date')]


        print("profile_skills : ", profile_skills)

        profile_certifications = [{
            'name': cert.certification.certification_name,
            'description': cert.certification.certification_description,
            'issued_year': cert.issued_date.year if cert.issued_date else None
        } for cert in ProfileCertification.objects.filter(profile_id=profile_id).order_by('-issued_date')]

        print("profile_certifications : " , profile_certifications)

        if request.GET.get('icims_job_id'):
            try: ejid = int(request.GET.get('icims_job_id'))
            except ValueError: ejid = None
            print("ejid : ", ejid)
            if ejid:
                employer_user = EmployerUser.objects.get(user=request.user)
                print("employer_user : ", employer_user)
                print("profile_id : ", profile_id)
                # EmployerProfileView(employer_user=employer_user,
                #                     employer_job_id=ejid,
                #                     profile_id=profile_id,
                #                     type='pdf_opened').save()
                print("EmployerProfileView saved-----------------")

        return {
            'education': profile_education,
            'experience' : profile_experience,
            'skills': profile_skills,
            'certifications': profile_certifications
        }


class ExportCandidatesView(LoginRequiredMixin, View):
    def get(self, request, icims_job_id):
        employer_job = EmployerJob.objects.get(id=icims_job_id)
        employer_user =  EmployerUser.objects.filter(user=request.user, employer=employer_job.employer).first()
        if employer_user is None:
            return None

        candidates_who_have_accepted = (EmployerCandidate.objects.filter(employer_job=employer_job,
                                                                         responded=True,
                                                                         accepted=True)
                                                                   .select_related('profile',
                                                                                   'profile__state')
                                                                   .order_by('profile_id'))

        fieldnames = ["profile_id", "first_name", "last_name", "email", "phone", "city", "state"]
        with io.StringIO() as file_out:
            csv_out = csv.DictWriter(file_out, fieldnames=fieldnames)

            # print header
            csv_out.writerow({key: key for key in fieldnames})

            for candidate in candidates_who_have_accepted:
                profile = candidate.profile
                collect_contact_info_for_profile(profile)
                e = ProfileEmail.to_reach(profile.id)
                p = ProfilePhoneNumber.to_reach(profile.id)
                dictionary = {
                    "profile_id": profile.id,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "email": e.value if e else None,
                    "phone": p.value if p else None,
                    "city": profile.city,
                    "state": profile.state.state_code,
                }
                csv_out.writerow(dictionary)

            response = HttpResponse(file_out.getvalue(), content_type="text/plain")

            # make browser download the file
            response['Content-Disposition'] = "attachment; filename=candidates_{}.csv".format(employer_job.id)

            record_event(request.user,
                         EventActions.employer_job_export,
                         {"employer_user_id": employer_user.id,
                          "icims_job_id": employer_job.id})

            return response



def get_common_certs_for_job(job):
    certs = Certification.objects.raw("""
    WITH
       job_certs AS (
           SELECT c.certification_id, c.profile_id FROM profile_job_mapping jm
           JOIN profile_certification c ON jm.profile_id=c.profile_id
           WHERE jm.job_id=%s
       ),
       common_ids AS (
           SELECT certification_id as id FROM job_certs
           GROUP BY certification_id
           ORDER BY count(profile_id) DESC
           LIMIT 20
       )
       SELECT c.* FROM common_ids
       JOIN certification c ON c.id=common_ids.id
       ORDER BY c.certification_name
    """, [job.id])

def convert_attached_skill_to_json(askill):
    skill = askill.skill

    return {
        "skill": {
            "id": skill.id,
            "skill_name": skill.skill_name
        },
        "default_weightage": askill.default_weightage,
        "experience_months": askill.experience_months
    }


def convert_attached_cert_to_json(acert):
    cert = acert.certification

    return {
        "certification": {
            "id": cert.id,
            "certification_name": cert.certification_name
        }
    }


def convert_skill_to_json(skill):
    return {
        "id": skill.id,
        "skill_name": skill.skill_name
    }


def convert_cert_to_json(cert):
    return {
        "id": cert.id,
        "certification_name": cert.certification_name
    }

def copy_skills_to_new_job(old_job, new_job):
    old_job_skills = JobSkill.objects.filter(job=old_job)
    new_job_skills = []

    for job_skill in old_job_skills:
        new_job_skill = JobSkill(job=new_job,
                                 skill=job_skill.skill,
                                 default_weightage=job_skill.default_weightage,
                                 experience_months=job_skill.experience_months)
        new_job_skills.append(new_job_skill)

    JobSkill.objects.bulk_create(new_job_skills)


def copy_certs_to_new_job(old_job, new_job):
    old_job_certs = JobCertification.objects.filter(job=old_job)
    new_job_certs = []

    for job_cert in old_job_certs:
        new_job_cert = JobCertification(job=new_job,
                                        certification=job_cert.certification)
        new_job_certs.append(new_job_cert)

    JobCertification.objects.bulk_create(new_job_certs)



def get_logo_url(logo_file_name):
    return settings.MEDIA_URL + logo_file_name


class CompanyDescriptionPostView(View):
    def post(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        employer = employer_user.employer

        employer.company_description = request.POST['company_description']
        employer.save()

        messages.success(request, 'Company description was set successfully.')
        return redirect("employer:email_settings")


@method_decorator(csrf_exempt, name='dispatch')
class FollowUpView(View):
    def post(self, request):
        if request.POST.get('token') == '123c7434-35f0-4690-adf4-9800e9249a0a':
            send_follow_up_emails()
            return HttpResponse("true")
        else:
            return HttpResponse("false")


class CandidateStatusView(LoginRequiredMixin, View):
    def get(self, request, candidate_id):
        employer_user = EmployerUser.objects.get(user=request.user)
        candidate = EmployerCandidate.objects.get(id=candidate_id)
        assert employer_user.employer_id == candidate.employer_job.employer_id

        values = []
        query = (EmployerCandidateStatus.objects
                                        .filter(employer_candidate=candidate)
                                        .order_by('-id')
                                        .values('id',
                                                'candidate_status__status',
                                                'date_created',
                                                'notes',
                                                'employer_user__user__first_name',
                                                'employer_user__user__last_name',
                                                'reject_reason__reason'))
        for record in query:
            employer_user_name = "{} {}".format(record['employer_user__user__first_name'],
                                                record['employer_user__user__last_name'])
            values.append({
                'id': record['id'],
                'status': record['candidate_status__status'],
                'date': record['date_created'].strftime('%Y-%m-%d %H:%M %p'),
                'employer_user_name': employer_user_name,
                'notes': record['notes'],
                'reject_reason': record['reject_reason__reason']
            })

        record_event(request.user,
                     EventActions.employer_candidate_status_open,
                     {"employer_id": employer_user.employer.id,
                      "employer_user_id": employer_user.id,
                      "employer_candidate_id": candidate.id})

        return HttpResponse(json.dumps(values),
                            content_type="application/json")



def change_candidate_status(request, employer_candidate_id, params):
    employer_user = EmployerUser.objects.get(user=request.user)
    candidate = EmployerCandidate.objects.get(id=employer_candidate_id)
    assert employer_user.employer_id == candidate.employer_job.employer_id

    new_status_id = int(params.get('new_status'))
    new_status_notes = params.get('new_status_notes')

    record = EmployerCandidateStatus(employer_candidate=candidate,
                                     candidate_status_id=new_status_id,
                                     employer_user=employer_user,
                                     notes=new_status_notes)

    reject_reason_id = int(request.POST.get('reject_reason') or 0)
    if reject_reason_id and new_status_id == 3:
        record.reject_reason_id = reject_reason_id

    record.save()

    record_event(request.user,
                 EventActions.employer_candidate_status_update,
                 {"employer_id": employer_user.employer.id,
                  "employer_user_id": employer_user.id,
                  "employer_candidate_id": candidate.id})

    return True



def has_user_favorited_any_candidates(user):
    return UserEvent.objects.filter(user=user, action="employer_job_candidate_add").exists()


def has_user_contacted_any_candidates(user):
    return UserEvent.objects.filter(user=user, action="employer_job_candidate_contact").exists()


class DismissTourView(View):
    def post(self, request, tour_name):
        employer_user = EmployerUser.objects.get(user=request.user)

        failed = False
        if tour_name == "jobs":
            employer_user.jobs_tour_dismissed = True
        elif tour_name == "jobdetail":
            employer_user.jobdetail_tour_dismissed = True
        elif tour_name == "search":
            employer_user.search_tour_dismissed = True
        else:
            failed = True

        if failed:
            return HttpResponse("false")
        else:
            employer_user.save()
            return HttpResponse("true")


class IcimsCandidateStatusDetailView(View):

    def post(self, request, employer_candidate_id):
        if change_candidate_status(request, employer_candidate_id, request.POST):
            messages.success(request, "Candidate status saved successfully.")
        else:
            messages.error(request, "There was an error.")

        return redirect('employer:candidate_status_detail', employer_candidate_id)

    def get(self, request, employer_candidate_id):
        employer_user = EmployerUser.objects.get(user=request.user)
        candidate = EmployerCandidate.objects.get(id=employer_candidate_id)
        job = candidate.employer_job

        if employer_user.employer_id != candidate.employer_job.employer_id:
            return error_page(request,
                              "Your account is not authorized to view that candidate.")

        records = []
        query = (EmployerCandidateStatus.objects
                                        .filter(employer_candidate=candidate)
                                        .order_by('-id')
                                        .values('id',
                                                'candidate_status__status',
                                                'date_created',
                                                'notes',
                                                'employer_user__user__first_name',
                                                'employer_user__user__last_name'))
        for record in query:
            employer_user_name = "{} {}".format(record['employer_user__user__first_name'],
                                                record['employer_user__user__last_name'])
            print(record)
            records.append({
                'id': record['id'],
                'status': record['candidate_status__status'],
                'date': record['date_created'].strftime('%Y-%m-%d %H:%M %p'),
                'employer_user_name': employer_user_name,
                'notes': record['notes'],
            })

        context = {
            "records": records,
            "candidate_name": "{} {}".format(candidate.profile.first_name, candidate.profile.last_name),
            "statuses": LookupCandidateStatus.objects.all().order_by('order'),
            "employer_candidate_id": candidate.id,
            "job_name": job.job_name,
            "job_id": job.id
        }

        record_event(request.user,
                     EventActions.employer_candidate_status_open,
                     {"employer_id": employer_user.employer.id,
                      "employer_user_id": employer_user.id,
                      "employer_candidate_id": candidate.id})

        return render(request, "icims/candidate_status_detail.html", context)


def extract_inline_images(content):
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(content), parser)

    root = tree.getroot()
    images = root.xpath(".//img")

    for img in images:
        src = img.get("src")
        url = upload_data_image(src)
        if url:
            img.set("src", url)

    markup = etree.tostring(root, encoding="unicode")
    return markup.replace("<html><body>", "").replace("</body></html>", "")


def upload_data_image(src):
    pattern = re.compile(r"data:image/(\w+);base64,(.*)")
    match = pattern.match(src)

    if match:
        extension, base64_contents = match.groups()
        filename = str(uuid.uuid4()).replace("-", "") + '.' + extension

        decoded_image = base64.decodebytes(base64_contents.encode('utf8'))

        file_io = FileIO()
        file_io.upload_file(filename,
                            decoded_image,
                            folder_name=EMPLOYER_ASSETS_FOLDER,
                            public=True)

        return "{}{}/{}".format(settings.MEDIA_URL, EMPLOYER_ASSETS_FOLDER, filename)
    else:
        return None


class RestrictProfileView(View):
    def post(self, request, profile_id):
        employer = EmployerUser.objects.get(user=request.user).employer

        if not (EmployerRestrictedProfile.objects
                                         .filter(employer=employer,
                                                 profile_id=profile_id)
                                         .exists()):
            EmployerRestrictedProfile(employer=employer,
                                      profile_id=profile_id).save()

        return HttpResponse("true")


def get_date_to_display_for_candidate_dict(candidate):
    if candidate['accepted_date']:
        return candidate['accepted_date']
    elif candidate['rejected_date']:
        return candidate['rejected_date']
    elif candidate['contacted_date']:
        return candidate['contacted_date']
    else:
        return candidate['date_created']


def error_page(request, message):
    return render(request, "generic_error.html", {"error_message": message})


class PreviouslyViewedProfilesView(View):
    @json_result
    def post(self, request):
        params = json.loads(request.body.decode('utf8'))
        employer_user = EmployerUser.objects.get(user=request.user)
        employer_job = EmployerJob.objects.get(id=params['icims_job_id'])
        assert employer_job.employer_id == employer_user.employer_id
        profile_ids = params['profile_ids']

        viewed_profile_ids = (EmployerProfileView.objects
                                                 .filter(employer_user=employer_user,
                                                         employer_job=employer_job,
                                                         profile_id__in=profile_ids)
                                                 .values_list('profile_id', flat=True)
                                                 .distinct())
        # print("@@@", viewed_profile_ids.query)
        return {profile_id: True
                for profile_id in viewed_profile_ids}


class IcimsStatsView(View):
    def get(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        employer_id = employer_user.employer_id
        return stats_manager_views.EmployerView().get(request, employer_id, True)
