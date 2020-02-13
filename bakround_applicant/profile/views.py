# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import json
import uuid
import logging
from datetime import datetime

import allauth.account.utils

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.conf import settings
from django.db import transaction
from django.db.models.aggregates import Count, Sum
from django.db.models import Q, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
from django.views import View
from django.template.loader import render_to_string

from bakround_applicant.all_models.dto import ProfileDataSchema, ProfileData
from bakround_applicant.all_models.db import Score, Profile, ProfileEducation, ProfileSkill, ProfileExperience, \
    ProfileCertification, LookupState, LookupCountry,  ProfileViewer, ProfileViewerAction, \
    LookupDegreeType, LookupDegreeMajor, LookupDegreeName, Skill, Job, LookupPhysicalLocation, \
    Certification, JobCertification, SME, JobSkill, EmailAddress, ProfileResume, ProfileEmail, \
    EmployerUser, EmployerProfileView, EmployerJob, ProfileJobMapping, ProfilePhoneNumber

from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile

from . import representation
from . import profile_search
from .profile_search import handle_profile_search_request,handle_icims_profile_search_request, make_initials_for_profile_id
from ..event import record_event, EventActions

from bakround_applicant.utilities.functions import json_result, pdf_result, employer_flag_required, \
                                                   has_candidate_accepted_request_for_job_associated_with_user

@method_decorator(employer_flag_required, name='dispatch')
@method_decorator(gzip_page, name='dispatch')
class SearchView(LoginRequiredMixin, View):
    @json_result
    def get(self, request):
        print("Inside SearchView get function")
        return handle_profile_search_request(request.GET, user=request.user)

    @json_result
    def post(self, request):
        print("Inside SearchView post function")
        params = json.loads(request.body.decode('utf8'))
        print("params: ", params)
        return handle_profile_search_request(params, user=request.user)


@method_decorator(employer_flag_required, name='dispatch')
@method_decorator(gzip_page, name='dispatch')
class IcimsSearchView(LoginRequiredMixin, View):
    @json_result
    def get(self, request):
        print("Inside IcimsSearchView get function")
        return handle_icims_profile_search_request(request.GET, user=request.user)

    @json_result
    def post(self, request):
        print("Inside IcimsSearchView post function")
        params = json.loads(request.body.decode('utf8'))
        print("params: ", params)
        params['city'] = ''
        params['state'] = ''
        return handle_icims_profile_search_request(params, user=request.user)


def detail_view_request_to_context(request, profile_id):
    sme_token = request.GET.get('token')

    employer_job_id = int(request.GET.get('ejid') or 0) or None
    hide_details = request.GET.get('hide_details') or False
    hide_bscore = request.GET.get('hide_bscore') or False
    hide_job = request.GET.get('hide_job') or False
    hide_profile_id = request.GET.get('hide_profile_id', True)

    if sme_token and SME.objects.filter(guid=sme_token).exists():
        hide_details = True
    elif request.user and request.user.is_authenticated():
        if request.user.is_staff:
            hide_details = False
        elif request.user.is_employer and employer_job_id:
            hide_details = not EmployerCandidate.objects.filter(profile_id=profile_id,
                                                                accepted=True,
                                                                employer_job_id=employer_job_id).exists()

    context = representation.profile_to_json(profile_id,
                                             employer_job_id=employer_job_id,
                                             hide_details=hide_details,
                                             hide_job=hide_job,
                                             hide_bscore=hide_bscore,
                                             hide_profile_id=hide_profile_id)

    if request.user:
        record_event(request.user,
                     EventActions.profile_printview_generate,
                     {"viewed_profile_id": profile_id,
                      "viewed_user_id": request.user.id})

        if employer_job_id and request.user.is_authenticated():
            for employer_user in EmployerUser.objects.filter(user=request.user):
                EmployerProfileView(employer_user=employer_user,
                                    employer_job_id=employer_job_id,
                                    profile_id=profile_id,
                                    type='pdf_opened').save()
    return context

def icims_detail_view_request_to_context(request, profile_id):
    sme_token = request.GET.get('token')

    icims_job_id = int(request.GET.get('ejid') or 0) or None
    hide_details = request.GET.get('hide_details') or False
    hide_bscore = request.GET.get('hide_bscore') or False
    hide_job = request.GET.get('hide_job') or False
    hide_profile_id = request.GET.get('hide_profile_id', True)

    if sme_token and SME.objects.filter(guid=sme_token).exists():
        hide_details = True
    elif request.user and request.user.is_authenticated():
        if request.user.is_staff:
            hide_details = False
        elif request.user.is_employer and icims_job_id:
            hide_details = not EmployerCandidate.objects.filter(profile_id=profile_id,
                                                                accepted=True,
                                                                employer_job_id=icims_job_id).exists()

    context = representation.profile_to_json_icims(profile_id,
                                             icims_job_id=icims_job_id,
                                             hide_details=hide_details,
                                             hide_job=hide_job,
                                             hide_bscore=hide_bscore,
                                             hide_profile_id=hide_profile_id)

    if request.user:
        record_event(request.user,
                     EventActions.profile_printview_generate,
                     {"viewed_profile_id": profile_id,
                      "viewed_user_id": request.user.id})

        if icims_job_id and request.user.is_authenticated():
            for employer_user in EmployerUser.objects.filter(user=request.user):
                EmployerProfileView(employer_user=employer_user,
                                    employer_job_id=icims_job_id,
                                    profile_id=profile_id,
                                    type='pdf_opened').save()
    return context


class HTMLDetailView(View):
    def get(self, request, profile_id):
        context = detail_view_request_to_context(request, profile_id)
        return render(request, 'profile/representation.html', context=context)

class JSONDetailView(View):
    @json_result
    def get(self, request, profile_id):
        return detail_view_request_to_context(request, profile_id)

class PDFDetailView(View):
    @pdf_result
    def get(self, request, profile_id):
        print("inside PDFDetailView get function----------------")
        print("request : ", request)
        context = detail_view_request_to_context(request, profile_id)
        print("context : ", context)
        return render_to_string('profile/representation.html', context=context)

class IcimsPDFDetailView(View):
    @pdf_result
    def get(self, request, profile_id):
        print("inside IcimsPDFDetailView get function----------------")
        print("request : ", request)
        context = icims_detail_view_request_to_context(request, profile_id)
        print("context : ", context)
        return render_to_string('profile/representation.html', context=context)
