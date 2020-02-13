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

from bakround_applicant.profile.profile_search import convert_profile_to_json, make_search_profile_model, \
                                     annotate_profiles_with_distance, convert_decimal_to_float, get_location_for_city, make_queryset_of_search_profiles, convert_page_to_json, list_candidates_for_job

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


class EmployerEditJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def post(self, request, employer_job_id=None):
        job_status_updated = False
        form = JobForm(request.POST)

        employer_user = EmployerUser.objects.get(user=request.user)
        form.limit_jobs_to_employer(employer_user.employer_id)

        if form.is_valid():
            job_id = string.capwords(form.cleaned_data['job'])

            city = string.capwords(form.cleaned_data['city'])
            if not validate_job_location(city, form.cleaned_data['state']):
                messages.error(request, 'Please enter a valid city/state combo.')
                return JobSettingsView().get(request,
                                             employer_job_id=employer_job_id,
                                             previous_form=form)

            # if not is_employer_job_location_distinct(employer_user.employer_id, job_id, city, form.cleaned_data['state'], [int(employer_job_id)]):
            #     if does_closed_job_exist_for_location(employer_user.employer_id, job_id, city, form.cleaned_data['state'], [int(employer_job_id)]):
            #         messages.error(request, 'This job already exists for the city you’ve chosen, but has been closed. Please re-activate the existing job by clicking on All Jobs on the Welcome page.')
            #     else:
            #         messages.error(request, 'A job of this type already exists for the same city/state combo.')
            #     return JobSettingsView().get(request,
            #                                  employer_job_id=employer_job_id,
            #                                  previous_form=form)

            if 'notifications' not in request.POST:
                messages.error(request, 'Please select at least one user to receive notifications.')
                return JobSettingsView().get(request,
                                             employer_job_id=employer_job_id,
                                             previous_form=form)

            employer_job = EmployerJob.objects.get(pk=employer_job_id)

            assert can_user_access_job(request.user, employer_job)

            job = Job.objects.get(id=job_id)

            employer_job.job = job
            employer_job.job_name = form.cleaned_data['job_name']
            employer_job.city = city
            employer_job.state_id = form.cleaned_data['state']

            if employer_job.open != bool(form.cleaned_data['open']):
                job_status_updated = True
            employer_job.open = form.cleaned_data['open']

            if 'custom_email_body' in form.cleaned_data:
                data = form.cleaned_data['custom_email_body']
                employer_job.custom_email_body = extract_inline_images(data) if data.strip() != '' else None

                if employer_job.custom_email_body is not None and EMPLOYER_LOGO_HTML_TAG in employer_job.custom_email_body:
                    if employer_job.employer.logo_file_name is None:
                        messages.error(request, 'Please upload a logo before inserting the logo tag.')
                        return redirect("employer:email_settings")
                    employer_job.custom_email_body = employer_job.custom_email_body.replace(EMPLOYER_LOGO_HTML_TAG, get_logo_image_html(logo_url=get_logo_url(employer_job.employer.logo_file_name)))

            employer_job.job_description = form.cleaned_data['job_description']
            employer_job.save()

            notification_user_ids = list(map(int, request.POST.getlist('notifications')))

            existing_notification_users = EmployerJobUser.objects.filter(employer_job=employer_job).values_list('employer_user_id', flat=True)

            users_to_add = list(set(notification_user_ids) - set(existing_notification_users))
            users_to_remove = list(set(existing_notification_users) - set(notification_user_ids))

            for user_id in users_to_add:
                try:
                    employer_user = EmployerUser.objects.get(pk=user_id)
                    employer_job_user = EmployerJobUser(employer_job_id=employer_job.id,
                                                    employer_user=employer_user,
                                                    added_by=employer_user)

                    employer_job_user.save()
                except:
                    pass

            for user_id in users_to_remove:
                try:
                    employer_user = EmployerUser.objects.get(pk=user_id)
                    employer_job_user = EmployerJobUser.objects.filter(employer_job_id=employer_job.id,
                                                    employer_user=employer_user).first()

                    employer_job_user.delete()
                except:
                    pass

            messages.success(request, 'Job updated successfully.')

            record_event(request.user,
                         EventActions.employer_job_update,
                         {"employer_job_id": employer_job.id})
            if job_status_updated:
                if employer_job.open:
                    record_event(request.user,
                         EventActions.employer_job_reopened,
                         {"employer_job_id": employer_job.id})
                else:
                    record_event(request.user,
                         EventActions.employer_job_closed, {"employer_job_id": employer_job.id})
        else:
            messages.error(request, 'Please fix the validation errors and try again.')

        return redirect("employer:job_settings", employer_job_id=employer_job_id)


class EmployerAddJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

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

        return render(request, "employer/add_job.html", context)

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
                        return redirect("employer:add_job")
                    employer_job.custom_email_body = employer_job.custom_email_body.replace(EMPLOYER_LOGO_HTML_TAG, get_logo_image_html(logo_url=get_logo_url(employer_job.employer.logo_file_name)))

                # replace tags like {CITY}, etc.
                employer_job.custom_email_body = replace_tags_in_initial_custom_email(employer_job.custom_email_body,
                                                                                      employer_job)


            employer_job.save()

            notification_user_ids = list(map(int, request.POST.getlist('notifications')))
            for user_id in notification_user_ids:
                try:
                    employer_user = EmployerUser.objects.get(pk=user_id)
                    employer_job_user = EmployerJobUser(employer_job_id=employer_job.id,
                                                    employer_user=employer_user,
                                                    added_by=employer_user)

                    employer_job_user.save()
                except:
                    pass

            messages.success(request, 'Job added successfully.')

            record_event(request.user,
                     EventActions.employer_job_create,
                     {"employer_job_id": employer_job.id})

            return redirect("employer:search", employer_job_id=employer_job.id)
        else:
            messages.error(request, 'Please fix the validation errors and try again.')

            return redirect("employer:add_job")

class EmployerPreviewCandidateContact(LoginRequiredMixin, View):
    def get(self, request, employer_job_id):
        profile_id = int(request.GET.get('profile_id') or 0)

        employer_user = get_employer_user(request.user.id)
        employer_job = EmployerJob.objects.get(id=int(employer_job_id))
        profile = Profile.objects.get(id=profile_id)

        mock_candidate = EmployerCandidate(profile=profile, employer_job=employer_job, employer_user=employer_user)
        n = email.ContactCandidate().build(employer_candidate=mock_candidate)
        context = {
            'subject': n.subject,
            'body': n.body,
            'metadata': n.metadata
        }
        return render(request, 'employer/preview_candidate_contact.html', context)


class EmployerIndexView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def get(self, request):

        return redirect("employer:jobs")

        # employer_id = EmployerUser.objects.filter(user=request.user).first().employer_id
        #
        # context = {
        #             "trial_days": utils.get_employer_trial_days_remaining(employer_id),
        #             "subscription_plan": utils.get_subscription_plan_for_user(request.user)
        #         }
        #
        # return render(request, "employer/index.html", context)

    def dispatch(self, *args, **kwargs):
        return super(EmployerIndexView, self).dispatch(*args, **kwargs)


class EmployerJobsView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def dispatch(self, *args, **kwargs):
        return super(EmployerJobsView, self).dispatch(*args, **kwargs)

    def get(self, request):

        employer_user = get_employer_user(request.user.id)

        current_plan = utils.get_subscription_plan_for_employer(employer_user.id)
        is_paid_plan = current_plan != 'bestfit-trial'

        employer_jobs = (EmployerJob.objects.filter(employer_id=employer_user.employer_id,
                                                    visible=True)
                                            .order_by('job_name')
                                            .prefetch_related('state'))

        restricted_profile_ids = EmployerRestrictedProfile.objects.filter(employer_id=employer_user.employer_id)\
            .values_list('profile_id', flat=True)

        job_candidates = {}
        job_total_candidate_count = list(EmployerCandidate.objects
                                   .filter(employer_job__employer_id=employer_user.employer_id,
                                           employer_job__visible=True,
                                           visible=True)
                                   .exclude(profile_id__in=restricted_profile_ids)
                                   .values('employer_job_id')
                                   .annotate(candidate_count=Count('id')))

        print("job_total_candidate_count : ", job_total_candidate_count)

        job_accepted_candidate_count = list(EmployerCandidate.objects
                                   .filter(employer_job__employer_id=employer_user.employer_id,
                                           employer_job__visible=True,
                                           visible=True,
                                           responded=True,
                                           accepted=True)
                                   .exclude(profile_id__in=restricted_profile_ids)
                                   .values('employer_job_id')
                                   .annotate(candidate_count=Count('id')))

        for index, item in enumerate(job_total_candidate_count):
            job_candidates[item['employer_job_id']] = {}
            job_candidates[item['employer_job_id']]['total_count'] = item['candidate_count']
            job_candidates[item['employer_job_id']]['accepted_count'] = get_first_matching(job_accepted_candidate_count, 'employer_job_id', item['employer_job_id'], 'candidate_count')

        states = LookupState.objects.all().order_by('state_code')

        employer_jobs_dictionary = {}
        employer_jobs_location_dictionary = defaultdict(list)
        for emp_job in employer_jobs:
            location = "{}, {}".format(emp_job.city, emp_job.state.state_code)
            employer_jobs_location_dictionary[location].append(emp_job)

            employer_jobs_dictionary[emp_job.id] = emp_job
            emp_job.recruiters = []

        eju_records = (EmployerJobUser.objects
                                      .filter(employer_job__employer_id=employer_user.employer_id,
                                              employer_job__visible=True,
                                              employer_user__is_bakround_employee=False)
                                      .select_related('employer_user__user')
                                      .order_by('employer_user__user__first_name',
                                                'employer_user__user__last_name'))
        for eju in eju_records:
            employer_jobs_dictionary[eju.employer_job_id].recruiters.append(eju.employer_user)

        my_jobs = get_jobs_for_employer_user(employer_user).only('id')
        my_job_ids = set(job.id for job in my_jobs)

        def is_any_job_initially_visible(_jobs):
            return any(job.open and (job.id in my_job_ids)
                       for job in _jobs)

        employer_jobs_by_location = sorted(({"location": location,
                                             "jobs": jobs,
                                             "initially_visible": is_any_job_initially_visible(jobs)}
                                            for (location, jobs) in employer_jobs_location_dictionary.items()),
                                           key=lambda x: (-len(x["jobs"]), x["location"]))

        context = {
            'employer_jobs': employer_jobs,
            'states': states,
            'job_candidates': job_candidates,
            'first_name': employer_user.user.first_name if employer_user.user else '',
            'employer_user': employer_user,
            'employer_jobs_by_location': employer_jobs_by_location,
            'tour_dismissed': employer_user.jobs_tour_dismissed,
            'my_job_ids': my_job_ids,
            'is_paid_plan': is_paid_plan
        }

        return render(request, "employer/jobs.html", context)


class EmployerJobDetailView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, employer_job_id):
        job = EmployerJob.objects.get(pk=employer_job_id)
        job_profile = job.job
        employer_user = get_employer_user(request.user.id)

        if job.employer_id != employer_user.employer_id:
            return error_page(request, "Your account is not authorized to view that job.")

        context = {
            'job': job,
            'application_inbox': get_application_inbox(job.guid),
            'props': json.dumps({
                'tour_dismissed': employer_user.jobdetail_tour_dismissed,
                'employer_job_id': job.id,
                'job_profile': { 'id': job_profile.id, 'job_name': job_profile.job_name },
                'job_open': job.open,
                'city': job.city,
                'state': job.state.state_code
            })
        }

        if not job.open:
            messages.error(request, 'This job is currently closed. Please go to the Job Settings page if you wish to re-open the job.')

        return render(request, "employer/job_detail.html", context)

class EmployerJobCandidatesListView(LoginRequiredMixin, View):
    def go(self, request, employer_job_id, params):
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

        employer_job = EmployerJob.objects.filter(id=employer_job_id).first()

        if not employer_job:
            return {'success': False}

        fake_ecs = EmployerCandidate.objects.filter(**({**q, 'employer_job_id': employer_job_id}))
        total = fake_ecs.count()
        total_interested = fake_ecs.filter(accepted=True).count()

        qs = list_candidates_for_job(employer_job_id, page, per_page, q, ordering)

        return { 'success': True, 'results': convert_page_to_json(page, qs, serialize=False), 'count': total, 'count_interested': total_interested }

    @json_result
    def get(self, request, employer_job_id):
        return self.go(request, employer_job_id, request.GET)

    @json_result
    def post(self, request, employer_job_id):
        params = json.loads(request.body.decode('utf8'))
        return self.go(request, employer_job_id, params)

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

class ProfileSearchView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    title = 'EmployerSearchView'
    template = 'employer/search.html'

    def get(self, request, employer_job_id):
        employer_user = EmployerUser.objects.get(user=request.user)

        job = EmployerJob.objects.get(pk=employer_job_id)
        job_profile = job.job

        if job.employer_id != employer_user.employer_id:
            return error_page(request, "Your account is not authorized to view that job.")

        state_list = list(LookupState.objects
                                     .filter(country__country_code="US")
                                     .order_by('state_code')
                                     .values("id", "state_name", "state_code"))

        if job_profile.accuracy is not None and job_profile.accuracy < 2 and not employer_user.employer.is_demo_account:
            messages.info(request, 'Note: This job is in beta mode and the bScore values may not be accurate.')

        context = {
            'title': self.title,
            'props': json.dumps({
                'state_list': state_list,
                'job_id': job.id,
                'job_profile': {'id': job_profile.id, 'job_name': job_profile.job_name},
                'city': job.city,
                'state': job.state.state_code,
                'tour_dismissed': employer_user.search_tour_dismissed,
                'show_advanced_search': False # TODO: bring this back!
            }),
            'employer_job_id': employer_job_id,
            'job': job,
            'employer': employer_user.employer
        }

        return render(request, self.template, context)

class CandidateFeedbackView(View):
    @json_result
    def post(self, request):
        params = json.loads(request.body.decode('utf8'))
        ids = params.get("ids", [])
        return { record.profile_id: int(record.bscore_value)
                                  for record in
                                  EmployerCandidateFeedback.objects
                                     .filter(profile_id__in=ids)
                                     .only('profile_id', 'bscore_value')
                                     .order_by('profile_id', 'id')
                                     .distinct('profile_id')}


class ProfileSummaryView(View):
    def make_date_range_for_exp(self, exp, missing = "???"):
        if not exp.start_date and not exp.end_date and not exp.is_current_position:
            return None

        start = exp.start_date.strftime("%B %Y") if exp.start_date else None
        end = "Present" if exp.is_current_position else (exp.end_date.strftime("%B %Y") if exp.end_date else None)
        return "{} - {}".format(start or missing, end or missing)

    @json_result
    def get(self, request, profile_id):
        profile_education = [{
            'school_name': pe.school_name,
            'school_type': pe.school_type,
            'degree_major': pe.degree_major.degree_major_name if pe.degree_major else pe.degree_major_other,
            'degree_name': pe.degree_name.degree_name if pe.degree_name else pe.degree_name_other,
            'degree_year': pe.degree_date.year if pe.degree_date else None
        } for pe in ProfileEducation.objects.filter(profile_id=profile_id).order_by('-degree_date')]

        profile_experience_qs = (ProfileExperience.objects
                                               .filter(profile_id=profile_id)
                                               .order_by('-is_current_position',
                                                         F('end_date').desc(nulls_first=True),
                                                         F('start_date').desc(nulls_last=True)))

        profile_experience = [{
            'date_range': self.make_date_range_for_exp(pe),
            'company_name': pe.company_name,
            'position_title': pe.position_title
        } for pe in profile_experience_qs]

        profile_skills = [{
            'name': skill.skill.skill_name,
            'experience_months': skill.experience_months,
        } for skill in ProfileSkill.objects.filter(profile_id=profile_id).order_by('-last_used_date')]

        profile_certifications = [{
            'name': cert.certification.certification_name,
            'description': cert.certification.certification_description,
            'issued_year': cert.issued_date.year if cert.issued_date else None
        } for cert in ProfileCertification.objects.filter(profile_id=profile_id).order_by('-issued_date')]

        if request.GET.get('employer_job_id'):
            try: ejid = int(request.GET.get('employer_job_id'))
            except ValueError: ejid = None

            if ejid:
                employer_user = EmployerUser.objects.get(user=request.user)
                EmployerProfileView(employer_user=employer_user,
                                    employer_job_id=ejid,
                                    profile_id=profile_id,
                                    type='pdf_opened').save()

        return {
            'education': profile_education,
            'experience' : profile_experience,
            'skills': profile_skills,
            'certifications': profile_certifications
        }


class RemoveCandidateFromJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    @json_result
    def post(self, request):
        params = json.loads(request.body.decode('utf8'))

        employer_job_id = params['employer_job_id']
        profile_id = params['profile_id']

        employer_candidate = EmployerCandidate.objects.filter(
            employer_job_id=employer_job_id,
            profile_id=profile_id).first()

        if employer_candidate:
            employer_candidate.visible = False
            employer_candidate.save()

            record_event(request.user,
                         EventActions.employer_job_candidate_remove,
                         {"employer_job_id": employer_job_id,
                          "employer_candidate_id": employer_candidate.id,
                          "profile_id": profile_id})

        return {'success': True}


class AddCandidateToJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    """Implement the backend logic behind the send 'Send Intro'"""
    @json_result
    def post(self, request):
        params = json.loads(request.body.decode('utf8'))

        employer_job_id = params['employer_job_id']
        should_contact = params.get('contact', False)

        # For simplicity's sake, 'assign' the candidate to the authenticated user.
        # This is making the assumption that the authenticated user is the right recruiter.
        employer_user = EmployerUser.objects.get(user=request.user)

        # Collect profile ids from the JSON POST body

        profile_ids = list(map(int, params.get('profile_ids', [])))
        if params.get('profile_id'):
            profile_ids.append(int(params['profile_id']))

        # We can't fail to add 0 candidates to a job!
        if len(profile_ids) == 0:
            return {"success": True, "contact_limit_hit": False}

        # TODO: this might be broken.
        for profile_id in profile_ids:
            ec = add_candidate_to_job(profile_id, request.user, employer_job_id, employer_user)
            if should_contact:
                contact_candidate(ec)

        return {"success": True, "contact_limit_hit": False}

class AssignUsersToJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, employer_job_id):
        employer_job = EmployerJob.objects.get(id=employer_job_id)

        # Make sure that this user is allowed to see the job!
        assert can_user_access_job(request.user, employer_job)

        context = {"employer_job": employer_job,
                   "employer_users": EmployerUser.objects.filter(employer_id=employer_job.employer_id)
                                                            .annotate(user_first_name=F('user__first_name'))
                                                            .annotate(user_last_name=F('user__last_name')),
                   "employer_job_users": EmployerJobUser.objects.filter(employer_job=employer_job)
                                                                .annotate(user_first_name=F('employer_user__user__first_name'))
                                                                .annotate(user_last_name=F('employer_user__user__last_name'))
                                                                .order_by('user_last_name',
                                                                          'user_first_name')}

        return render(request, "employer/assign_users_to_job.html", context)


def can_user_access_job(user, employer_job):
    return EmployerUser.objects.filter(user=user,
                                       employer_id=employer_job.employer_id).exists()


class AddUserToJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    @json_result
    def post(self, request):
        employer_job = EmployerJob.objects.get(id=request.POST['employer_job_id'])

        assert can_user_access_job(request.user, employer_job)

        this_employer_user = get_employer_user(request.user.id)

        employer_user = EmployerUser.objects.get(pk=request.POST['employer_user_id'])

        assert employer_user.employer_id == employer_job.employer_id

        if EmployerJobUser.objects.filter(employer_job=employer_job,
                                          employer_user=employer_user).exists():
            return False
        else:
            EmployerJobUser(employer_job=employer_job,
                            employer_user=employer_user,
                            added_by=this_employer_user).save()
            return True


class RemoveUserFromJobView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    @json_result
    def post(self, request):
        employer_job = EmployerJob.objects.get(id=request.POST['employer_job_id'])

        assert can_user_access_job(request.user, employer_job)

        employer_user = EmployerUser.objects.get(pk=request.POST['employer_user_id'])

        assert employer_user.employer_id == employer_job.employer_id

        EmployerJobUser.objects.filter(employer_job=employer_job,
                                       employer_user=employer_user).delete()

        return True


class JobSettingsView(LoginRequiredMixin, SubscriptionRequiredMixin, View):

    def get(self, request, employer_job_id, previous_form=None):

        employer_job = EmployerJob.objects.get(pk=employer_job_id)
        employer_user = EmployerUser.objects.filter(user=request.user).first()
        employer = employer_user.employer

        assert employer_user is not None
        assert can_user_access_job(request.user, employer_job)

        custom_email_body = current_email_body = employer_job.custom_email_body or get_default_email_body(employer_job)
        if custom_email_body is not None:
            pattern = re.compile(r'''<img src=["']http([\w\W]+?)/>''')
            custom_email_body = re.sub(pattern, EMPLOYER_LOGO_HTML_TAG, custom_email_body)

        data = {'id': employer_job.id,
                'job': employer_job.job_id,
                'job_name': employer_job.job_name,
                'city': employer_job.city,
                'state': employer_job.state_id,
                'custom_email_body': custom_email_body,
                'open': employer_job.open,
                'job_description': employer_job.job_description}

        form = JobForm(initial=data)
        form.limit_jobs_to_employer(employer_user.employer_id)

        states = LookupState.objects.all().order_by('state_code')

        job_families = get_job_families_for_employer(employer)

        default_email_body = get_default_email_body(employer_job)

        employer_user_ids = list(EmployerJobUser.objects.filter(employer_job=employer_job).values_list('employer_user_id', flat=True))

        logo_url = None
        logo_file_name = employer_job.employer.logo_file_name
        if logo_file_name is not None:
            logo_url = get_logo_url(logo_file_name)

        if previous_form:
            form.initial['custom_email_body'] = previous_form.cleaned_data['custom_email_body']

        low_accuracy_jobs = list(Job.objects.filter(employer_id__isnull=True, accuracy__lt=2).values_list('id', flat=True))

        context = {"form": form,
                   "employer_job_id": employer_job_id,
                   "states": states,
                   "job_families": job_families,
                   "application_inbox": get_application_inbox(employer_job.guid),
                   "logo_url": logo_url,
                   "default_email_body": default_email_body,
                   "current_email_body": current_email_body,
                   "employer_job": employer_job,
                   "employer_user_id": employer_user.id,
                   "employer_user_ids": employer_user_ids,
                   "employer_users": EmployerUser.objects.filter(employer_id=employer_job.employer_id)
                                                            .annotate(user_first_name=F('user__first_name'))
                                                            .annotate(user_last_name=F('user__last_name'))
                                                            .order_by('user_first_name'),
                   "low_accuracy_jobs": low_accuracy_jobs,
                   "is_demo_account": employer.is_demo_account,
                   "can_edit_email": request.user.is_staff or employer_user.is_bakround_employee}

        return render(request, 'employer/job_settings.html', context)


class ExportCandidatesView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, employer_job_id):
        employer_job = EmployerJob.objects.get(id=employer_job_id)
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
                          "employer_job_id": employer_job.id})

            return response


class AddUserView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request):
        form = EmployerUserForm()

        employer = EmployerUser.objects.get(user=request.user).employer
        if not employer.auto_contact_enabled:
            form.fields['auto_contact_enabled'].widget = forms.HiddenInput()

        context = {"form": form,
                   "submit_label": "Add"}
        return render(request, "employer/add_user.html", context)

    def post(self, request):
        creator = EmployerUser.objects.get(user=request.user)
        employer = creator.employer
        form = EmployerUserForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            email = data['email'].strip()

            if User.objects.filter(email=email).exists():
                return redirect('employer:manage_employer_users')

            new_user = User.objects.create_user(username=email.replace("@", "___"),
                                                email=email,
                                                is_employer=True,
                                                first_name=data['first_name'],
                                                last_name=data['last_name'],
                                                initial_login_token=str(uuid.uuid4()))
            new_user.set_unusable_password()
            new_user.save()

            # also create profile?

            employer_user = EmployerUser(employer=employer,
                                         user=new_user,
                                         is_owner=bool(data.get('is_owner')),
                                         auto_contact_enabled=bool(data.get('auto_contact_enabled')),
                                         is_bakround_employee=email.endswith("@bakround.com"))
            employer_user.save()
            employer_user.custom_email_address = generate_custom_email_address(employer_user)
            employer_user.save()

            existing_emails = EmailAddress.objects.filter(email=email)
            if existing_emails.exists():
                existing_emails.update(verified=True)
            else:
                EmailAddress(user=new_user,
                             email=email,
                             verified=True).save()

            send_login_link_to_employer_user(employer_user, creator)
            record_event(request.user,
                         EventActions.employer_user_create,
                         {"employer_user_id": employer_user.id,
                          "user_id": new_user.id,
                          "email": email})

        messages.success(request, 'An invitation has been sent to the new user.')
        return redirect('employer:manage_employer_users')


class ManageUserView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request):
        employer = EmployerUser.objects.get(user=request.user).employer
        employer_user_list = list(EmployerUser.objects.filter(employer=employer)
                                                      .select_related('user')
                                                      .order_by('-is_owner',
                                                                'user__last_name',
                                                                'user__first_name'))
        for employer_user in employer_user_list:
            employer_user.can_delete = can_delete_employer_user(employer_user)

        context = {
            "employer_user_list": employer_user_list,
            "employer": employer,
        }
        return render(request, "employer/manage_users.html", context)


class EditUserView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, employer_user_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        employer_user_to_edit = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_to_edit.employer == employer

        data = {key: getattr(employer_user_to_edit.user, key)
                for key in ["first_name", "last_name", "email"]}
        data['is_owner'] = employer_user_to_edit.is_owner
        data['auto_contact_enabled'] = employer_user_to_edit.auto_contact_enabled
        form = EmployerUserForm(data)

        if not employer.auto_contact_enabled:
            form.fields['auto_contact_enabled'].widget = forms.HiddenInput()

        context = {"employer_user": employer_user_to_edit,
                   "employer": employer,
                   "form": form,
                   "submit_label": "Submit"}

        return render(request, "employer/add_user.html", context)

    def post(self, request, employer_user_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        employer_user_to_edit = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_to_edit.employer == employer

        form = EmployerUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = employer_user_to_edit.user

            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.save()

            employer_user_to_edit.is_owner = bool(data.get('is_owner'))
            if employer.auto_contact_enabled:
                employer_user_to_edit.auto_contact_enabled = bool(data.get('auto_contact_enabled'))
            employer_user_to_edit.save()

            record_event(request.user,
                         EventActions.employer_user_update,
                         {"employer_user_id": employer_user_to_edit.id,
                          "user_id": user.id})

        messages.success(request, 'User updated successfully.')
        return redirect('employer:manage_employer_users')


def send_login_link_to_employer_user(employer_user, creator):
    login_url = "{}/initial_login/{}".format(get_website_root_url(),
                                             employer_user.user.initial_login_token)
    context = {
        "login_url": login_url,
        "employer_user": employer_user,
        "creator": creator,
    }
    subject, body = render_to_string("email/new_user_information.html", context).split("\n", 1)

    sender = 'no-reply@bakround.com'
    reply_to = [creator.user.email]
    recipients = [employer_user.user.email]

    msg = EmailMessage(subject, body, sender, recipients, reply_to=reply_to)
    msg.content_subtype = "html"
    msg.send()


class ResendLoginTokenView(View):
    def post(self, request, employer_user_id):
        creator = EmployerUser.objects.get(user=request.user)
        employer_user = EmployerUser.objects.get(id=employer_user_id,
                                                 employer=creator.employer)

        if employer_user.user.initial_login_token:
            send_login_link_to_employer_user(employer_user, creator)
            return render(request,
                          "pages/generic_message.html",
                          {"message": "The email has been re-sent.",
                           "return_page": "employer:manage_employer_users"})
        else:
            return render(request,
                          "pages/generic_message.html",
                          {"message": "That user has already logged in.",
                           "return_page": "employer:manage_employer_users"})

    def get(self, request, *args, **kwargs):
        return redirect('employer:manage_employer_users')


class EmployerSignupView(View):
    def get(self, request):
        if request.user.is_authenticated():
            return redirect('home')

        context = {}
        context['form'] = EmployerSignupForm()

        return render(request, "employer/employer_signup.html", context)


class DeleteUserView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request, employer_user_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        employer_user_to_delete = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_to_delete.employer == employer

        if can_delete_employer_user(employer_user_to_delete):
            user = employer_user_to_delete.user
            user_id = user.id
            employer_user_to_delete.delete()
            user.delete()

            record_event(request.user,
                         EventActions.employer_user_delete,
                         {"employer_user_id": employer_user_id,
                          "user_id": user_id,
                          "email": user.email})

        messages.success(request, 'User has been removed from your account.')
        return redirect('employer:manage_employer_users')


def can_delete_employer_user(employer_user):
    return not EmployerCandidate.objects.filter(employer_user=employer_user, ).exists() \
        and employer_user.user.initial_login_token is not None


class CustomJobProfileIndexView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request):
        employer = EmployerUser.objects.get(user=request.user).employer
        standard_jobs = (Job.objects.filter(employer=None,
                                            job_family_id=employer.job_family_id)
                                    .order_by('job_name'))
        custom_jobs = list(Job.objects.filter(employer=employer).order_by('job_name'))
        job_descriptions = {job.id: (job.job_description or "")
                            for job in standard_jobs}

        for custom_job in custom_jobs:
            custom_job.can_delete = can_delete_custom_job(custom_job)

        context = {
            'standard_jobs': standard_jobs,
            'custom_jobs': custom_jobs,
            'job_descriptions_json': json.dumps(job_descriptions),
        }
        return render(request, 'employer/custom_jobs_index.html', context)


class CreateCustomJobProfileView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request):
        employer = EmployerUser.objects.get(user=request.user).employer

        job_name = request.POST['new_job_name']
        job_description = request.POST['job_description']

        parent_job_id = int(request.POST['parent_job_id'])
        parent_job = Job.objects.get(id=parent_job_id)
        assert parent_job.employer_id is None

        new_job = Job(job_name=job_name,
                      job_description=job_description,
                      employer=employer,
                      parent_job=parent_job,
                      job_family=parent_job.job_family,
                      has_ever_been_scored=False,
                      is_waiting_to_be_scored=True,
                      onet_position=parent_job.onet_position)
        new_job.save()

        copy_skills_to_new_job(parent_job, new_job)
        copy_certs_to_new_job(parent_job, new_job)

        record_event(request.user,
                         EventActions.employer_custom_job_create,
                         {"job_id": new_job.id,
                          "employer_id": new_job.employer_id})

        return redirect('employer:custom_job_profile_index')


def can_delete_custom_job(job):
    SearchProfile = make_search_profile_model()
    return not (EmployerJob.objects.filter(job=job).exists() or
                Profile.objects.filter(job=job).exists() or
                SearchProfile.objects.filter(job=job).exists())


class DeleteCustomJobProfileView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request, job_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        job = Job.objects.get(id=job_id)

        assert job.employer_id == employer.id and can_delete_custom_job(job)
        job.delete()

        record_event(request.user,
                         EventActions.employer_custom_job_delete,
                         {"job_id": job.id,
                          "employer_id": job.employer_id})

        return redirect('employer:custom_job_index')


class EditCustomJobProfileView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request, job_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        job = Job.objects.get(id=job_id)
        assert job.employer_id == employer.id

        attached_skills = job.jobskill_set.order_by('skill__skill_name')
        all_skills = Skill.objects.order_by('skill_name')

        attached_certs = job.jobcertification_set.order_by('certification__certification_name')
        all_certs = get_common_certs_for_job(job.parent_job)

        context = {
            "job": job,
            "possible_skill_weights": list(range(6)),

            "attached_skills": attached_skills,
            "attached_skills_json": json.dumps([convert_attached_skill_to_json(askill) for askill in attached_skills]),

            "all_skills": all_skills,
            "all_skills_json": json.dumps([convert_skill_to_json(skill) for skill in all_skills]),

            "attached_certs": attached_certs,
            "attached_certs_json": json.dumps([convert_attached_cert_to_json(acert) for acert in attached_certs]),

            "all_certs": all_certs,
            "all_certs_json": json.dumps([convert_cert_to_json(cert) for cert in all_certs]),
        }

        return render(request, 'employer/custom_job_edit.html', context)

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


class ModifyCustomJobProfileView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request, job_id):
        employer = EmployerUser.objects.get(user=request.user).employer
        job = Job.objects.get(id=job_id)
        assert job.employer_id == employer.id

        submitted_json = json.loads(request.POST['submitted_json'])
        new_job_name = submitted_json['job_name']
        new_job_description = submitted_json['job_description']

        need_to_rescore = False

        was_modified = False
        if job.job_name != new_job_name:
            job.job_name = new_job_name
            was_modified = True
        if job.job_description != new_job_description:
            job.job_description = new_job_description
            was_modified = True
        if was_modified:
            job.save()
            need_to_rescore = True

        skills_json = submitted_json['skills']

        old_job_skills = {}
        for old_job_skill in JobSkill.objects.filter(job=job):
            skill_id = old_job_skill.skill_id
            old_job_skills[skill_id] = {
                "default_weightage": old_job_skill.default_weightage,
                "experience_months": old_job_skill.experience_months,
            }

        new_job_skills = {}
        for new_job_skill in skills_json:
            skill_id = new_job_skill['skill_id']
            new_job_skills[skill_id] = new_job_skill

        for skill_id in old_job_skills:
            if skill_id not in new_job_skills:
                JobSkill.objects.get(job=job, skill_id=skill_id).delete()
                need_to_rescore = True

        for (skill_id, skill) in new_job_skills.items():
            (record, was_created) = JobSkill.objects.get_or_create(job=job, skill_id=skill_id)

            was_modified = False
            if record.default_weightage != skill['default_weightage']:
                record.default_weightage = skill['default_weightage']
                was_modified = True
            if record.experience_months != skill['experience_months']:
                record.experience_months = skill['experience_months']
                was_modified = True

            if was_modified or was_created:
                record.save()
                need_to_rescore = True

        certs_json = submitted_json['certs']
        old_job_certs = set(old_job_cert.certification_id
                            for old_job_cert in JobCertification.objects.filter(job=job))
        new_job_certs = set(new_job_cert['cert_id'] for new_job_cert in certs_json)

        for cert_id in old_job_certs:
            if cert_id not in new_job_certs:
                JobCertification.objects.get(job=job, certification_id=cert_id).delete()
                need_to_rescore = True

        for cert_id in new_job_certs:
            if cert_id not in old_job_certs:
                JobCertification(job=job,
                                 certification_id=cert_id).save()
                need_to_rescore = True

        if need_to_rescore:
            job.is_waiting_to_be_scored = True
            job.save()

        record_event(request.user,
                         EventActions.employer_custom_job_update,
                         {"job_id": job.id,
                          "employer_id": job.employer_id})

        messages.success(request,
                         "Job #{} was updated successfully.".format(job_id))
        return redirect('employer:custom_job_profile_index')


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


class EmailSettingsView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def get(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        employer = employer_user.employer

        # custom_email_body = current_email_body = get_default_email_body(employer=employer)

        # pattern = re.compile(r'''<img src=["']http([\w\W]+?)/>''')
        # custom_email_body = re.sub(pattern, EMPLOYER_LOGO_HTML_TAG, custom_email_body)

        logo_url = None
        if employer.logo_file_name is not None:
            logo_url = get_logo_url(employer.logo_file_name)

        context = {
            "logo_html_tag": EMPLOYER_LOGO_HTML_TAG,
            "logo_url": logo_url,
            # "custom_email_body": custom_email_body,
            # "current_email_body": current_email_body,
            "company_description": employer.company_description,
        }
        return render(request, "employer/email_settings.html", context)


class EmailSettingsBodyView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request):
        custom_email_body = request.POST['custom_email_body']

        employer_user = EmployerUser.objects.get(user=request.user)
        employer = employer_user.employer

        if custom_email_body is None or custom_email_body.strip() == '':
            custom_email_body = get_default_email_body(employer=employer)
            messages.info(request, 'Nothing was specified, so we''re defaulting back to the system message.')
        elif EMPLOYER_LOGO_HTML_TAG in custom_email_body:
            if employer.logo_file_name is None:
                messages.error(request, 'Please upload a logo before inserting the logo tag.')
                return redirect("employer:email_settings")
            custom_email_body = custom_email_body.replace(EMPLOYER_LOGO_HTML_TAG, get_logo_image_html(logo_url=get_logo_url(employer.logo_file_name)))
        employer.custom_email_body = extract_inline_images(custom_email_body)
        employer.save()

        record_event(request.user,
                     EventActions.employer_custom_email_body_save,
                     {"employer_id": employer.id})

        messages.success(request, 'Email body saved successfully.')
        return redirect("employer:email_settings")


class EmailSettingsLogoView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
    def post(self, request):
        form = UploadLogoForm(request.POST, request.FILES)
        if form.is_valid():

            employer_user = EmployerUser.objects.get(user=request.user)
            employer = employer_user.employer

            logo_file = request.FILES['file']

            # build a dictionary of metadata to save with the file
            metadata = {
                'employer_id': employer.id,
                'employer_user_id': employer_user.id
            }

            file_io = FileIO()

            uploaded_file_name = file_io.upload_file(generate_unique_file_name(logo_file.name),
                                                     logo_file.read(),
                                                     folder_name=EMPLOYER_ASSETS_FOLDER,
                                                     public=True,
                                                     metadata=metadata)

            if employer.logo_file_name is not None:
                try:
                    file_io.delete_file(file_name=employer.logo_file_name)
                except:
                    pass

            employer.logo_file_name = uploaded_file_name
            employer.save()

            record_event(request.user,
                         EventActions.employer_logo_upload,
                         {"file_name": uploaded_file_name,
                          "employer_id": employer.id,
                          "employer_user_id": employer_user.id})

            messages.success(request, 'Logo uploaded successfully.')
        else:
            messages.error(request, 'There was an error while uploading your logo.')

        return redirect("employer:email_settings")


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


class CandidateStatusView(LoginRequiredMixin, SubscriptionRequiredMixin, View):
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


class FetchPossibleStatusesView(View):
    @json_result
    def get(self, request):
        return [{"id": row.id, "status": row.status}
                  for row in LookupCandidateStatus.objects.order_by('order')]


class FetchPossibleRejectReasonsView(View):
    @json_result
    def get(self, request):
        return [{"id": row.id, "reason": row.reason}
                  for row in LookupRejectReason.objects.order_by('order')]


class ChangeCandidateStatusView(View):
    @json_result
    def post(self, request, candidate_id):
        change_candidate_status(request, candidate_id, json.loads(request.body.decode('utf-8')))
        return {'success': True}


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


class EmployerCandidateStatusDetailView(View):

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

        return render(request, "employer/candidate_status_detail.html", context)


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


class EmployerFeedbackSubmissionView(View):
    def post(self, request):
        params = request.POST

        employer_user = EmployerUser.objects.get(user=request.user)

        profile_id = int(params['profile_id'])

        employer_job_id = int(params['employer_job_id'])
        employer_job = EmployerJob.objects.get(id=employer_job_id)
        assert employer_job.employer_id == employer_user.employer_id

        comment = params.get('comment')
        should_interview = bool(params.get('should_interview'))

        bscore_raw = params.get('bscore_value')
        if bscore_raw is None or bscore_raw == '':
            bscore_value = None
        else:
            bscore_value = int(float(bscore_raw))

        actual_bscore = float(params['actual_bscore'])

        record = EmployerCandidateFeedback(profile_id=profile_id,
                                           employer_job=employer_job,
                                           employer_user=employer_user,
                                           bscore_value=bscore_value,
                                           comment=comment,
                                           should_interview=should_interview,
                                           saved_search_id=int(params['saved_search_id']) or None,
                                           candidate_ranking=params['candidate_ranking'],
                                           actual_bscore=actual_bscore)
        fill_in_checkbox_columns(record, params)

        record.save()
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


class EnableAutopilotView(View):
    def post(self, request, employer_job_id):
        # AN - disabling the ability to turn on/off auto-pilot for now
        return HttpResponse("false")

        employer_user = EmployerUser.objects.get(user=request.user)
        employer_job = EmployerJob.objects.get(id=employer_job_id)
        assert employer_job.employer_id == employer_user.employer_id

        enable = (request.POST['on'] == "1")
        employer_job.candidate_queue_enabled = enable
        employer_job.auto_contact_enabled = enable
        employer_job.save()

        return HttpResponse("true")


class NotificationSettings(View):
    def get(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        return render(request,
                      "employer/notification_settings.html",
                      {"employer_user": employer_user})

    def post(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        params = request.POST

        employer_user.daily_summary_email_enabled = bool(params.get('daily_summary_email_enabled'))
        employer_user.weekly_stats_email_enabled = bool(params.get('weekly_stats_email_enabled'))

        employer_user.save()

        return redirect('account_settings')


def error_page(request, message):
    return render(request, "generic_error.html", {"error_message": message})


class PreviouslyViewedProfilesView(View):
    @json_result
    def post(self, request):
        params = json.loads(request.body.decode('utf8'))
        employer_user = EmployerUser.objects.get(user=request.user)
        employer_job = EmployerJob.objects.get(id=params['employer_job_id'])
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


class DeleteJobView(View):
    def post(self, request, employer_job_id):
        employer_user = EmployerUser.objects.get(user=request.user)
        employer_job = EmployerJob.objects.get(id=employer_job_id)

        assert employer_job.employer_id == employer_user.employer_id
        assert not employer_job.open

        employer_job.visible = False
        employer_job.auto_contact_enabled = employer_job.candidate_queue_enabled = False

        employer_job.save()

        return HttpResponse("ok")


class GetHeadshotUrlView(View):
    @json_result
    def get(self, request, employer_user_id):
        employer_user_requesting = EmployerUser.objects.get(user=request.user)
        employer_user = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_requesting.employer_id == employer_user.employer_id

        return {
            "name": "{} {}".format(employer_user.user.first_name,
                                   employer_user.user.last_name),
            "url": employer_user.headshot_file_name,
        }


class HeadshotUploadForm(forms.Form):
    file = FileField(max_length=10485760)


class HeadshotUploadView(View):
    @json_result
    def post(self, request, employer_user_id):
        employer_user_requesting = EmployerUser.objects.get(user=request.user)
        employer_user = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_requesting.employer_id == employer_user.employer_id

        form = HeadshotUploadForm(request.FILES)
        if form.is_valid():
            img_file = request.FILES['file']

            output_file_name = "headshots/{}_{}".format(uuid.uuid4(),
                                                        img_file.name[:-50])

            file_io = FileIO()
            uploaded_file_name = file_io.upload_file(output_file_name,
                                                     img_file.read(),
                                                     public=True)

            employer_user.headshot_file_name = "{}{}".format(settings.MEDIA_URL, uploaded_file_name)
            employer_user.save()
            return {"success": True}
        else:
            return {"success": False}


class HeadshotRemovalView(View):
    @json_result
    def post(self, request, employer_user_id):
        employer_user_requesting = EmployerUser.objects.get(user=request.user)
        employer_user = EmployerUser.objects.get(id=employer_user_id)
        assert employer_user_requesting.employer_id == employer_user.employer_id

        employer_user.headshot_file_name = None
        employer_user.save()
        return {"success": True}


class EmployerStatsView(View):
    def get(self, request):
        employer_user = EmployerUser.objects.get(user=request.user)
        employer_id = employer_user.employer_id
        return stats_manager_views.EmployerView().get(request, employer_id, True)
