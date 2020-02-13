# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import json
import uuid
from datetime import datetime

import requests

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.utils import timezone
from django.forms import Form
from django.db.models import Q

from .util import choose_random_unreviewed_resume_for_sme, get_resume_reviews_for_sme_by_month

from bakround_applicant.employer.utils import add_candidate_to_job, contact_candidate
from bakround_applicant.all_models.db import EmployerJob, EmployerCandidate, ProfileCertification, ProfileEducation, ProfileExperience, ProfileSkill, \
                                             SME, SMEFeedback, SMEAction, SMEPayRate, ProfileResume, Job
from bakround_applicant.utilities.functions import make_employer_job_structure_for_dropdown, get_website_root_url

class SMEFeedbackIndexView(View):
    def show(self, request, params, submitted=False):
        token = params.get('token', '').replace(" ", "").replace("\n", "")
        context = {"submitted": submitted}

        if not token:
            context["error"] = "missing token"
        elif not SME.objects.filter(guid=token, active=True).exists():
            context["error"] = "bad token"
        else:
            sme = SME.objects.get(guid=token, active=True)

            context["token"] = token
            context["sme"] = sme
            if sme.employer_user:
                context["contact_form"] = SMEContactForm(sme.employer_user.employer)

            context["number_of_reviews_so_far"] = SMEFeedback.objects.filter(sme=sme).count()
            context["feedback_guid"] = str(uuid.uuid4())
            context["ask_about_low_scores"] = int(sme.ask_about_low_scores)

            if has_sme_reached_their_review_limit(sme):
                context["has_limit_been_reached"] = True
            else:
                resume = choose_random_unreviewed_resume_for_sme(sme)
                if resume:
                    context["resume"] = resume
                    context["resume_url"] = "/sme_feedback/view_resume/{}".format(resume.id)

                    SMEAction(sme_id=sme.id,
                              profile_resume_id=resume.id,
                              action_name='FEEDBACK_PAGE_OPENED').save()

                    if sme.employer_user:
                        already_contacted_candidate = search_for_already_contacted_candidate(sme.employer_user.employer,
                                                                                             resume.profile)
                        context["already_contacted_candidate"] = already_contacted_candidate

        return render(request, "sme_feedback/index.html", context)

    def get(self, request):
        return self.show(request, request.GET)

    def post(self, request):
        params = request.POST
        token = params.get('token')
        comment = params.get('comment')
        should_interview = bool(params.get('should_interview'))
        resume_id = params.get('resume_id')
        feedback_guid = params.get('feedback_guid', '')

        bscore_raw = params.get('bscore_value')
        if bscore_raw is None or bscore_raw == '':
            bscore_value = None
        else:
            bscore_value = int(float(bscore_raw))

        sme = SME.objects.get(guid=token)

        sme_pay_rate = SMEPayRate.objects.filter(sme_id=sme.id, effective_date__lte=timezone.now()).order_by('-effective_date').first()

        if not SMEFeedback.objects.filter(sme_id=sme.id,
                                          profile_resume_id=resume_id,
                                          feedback_guid=feedback_guid):
            feedback_row = SMEFeedback(sme_id=sme.id,
                        profile_resume_id=resume_id,
                        bscore_value=bscore_value,
                        comment=comment,
                        should_interview=should_interview,
                        sme_pay_rate=sme_pay_rate,
                        feedback_guid=feedback_guid)

            fill_in_checkbox_columns(feedback_row, request.POST)

            feedback_row.save()

            SMEAction(sme_id=sme.id,
                      profile_resume_id=resume_id,
                      action_name='FEEDBACK_SUBMITTED').save()

        return self.show(request, params, submitted=True)

class ViewResumeView(View):
     def get(self, request, resume_id):
        resume = ProfileResume.objects.filter(id=resume_id).first()
        if not resume:
            raise Http404

        if not resume.parser_output:
            raise Http404

        if isinstance(resume.parser_output, str):
            resume.parser_output = json.loads(resume.parser_output)
            resume.save()

        return render(request, "sme_feedback/resume.html", { "resume_data": resume.parser_output })

# Tracks opening resumes (the open resume link)
class SMEOpenResumeView(View):
    def post(self, request):
        data = json.loads(request.body.decode('UTF-8'))

        sme_id = data['sme_id']
        profile_resume_id = data['profile_resume_id']

        if sme_id is not None and profile_resume_id is not None:
            SMEAction(sme_id=sme_id,
                      profile_resume_id=profile_resume_id,
                      action_name='RESUME_OPENED').save()

        return HttpResponse(status=200)


def has_sme_reached_their_review_limit(sme):
    if sme.review_limit is None:
        return False
    else:
        return number_of_reviews_performed_by_sme(sme) >= sme.review_limit


def number_of_reviews_performed_by_sme(sme):
    return sme.smefeedback_set.count()


CHECKBOX_COLUMNS = ["wrong_job", "wrong_language", "incomplete",
                    "insuff_exp", "insuff_skills", "insuff_certs",
                    "unknown_employers", "unknown_schools"]


def fill_in_checkbox_columns(row, parameters):
    for column in CHECKBOX_COLUMNS:
        value = bool(parameters.get("column_" + column))
        setattr(row, column, value)


class SMEDoNotAskAgainView(View):
    def post(self, request):
        guid = request.POST['guid']
        sme = SME.objects.get(guid=guid)
        sme.ask_about_low_scores = False
        sme.save()
        return HttpResponse("true")

class EmployerJobModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.job_name


class SMEContactForm(Form):
    employer_job = ChoiceField([])

    def __init__(self, employer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employer_job'].choices = make_employer_job_structure_for_dropdown(True, employer_id=employer.id)


class SMEContactCandidate(View):
    def post(self, request):
        sme = SME.objects.get(guid=request.POST['sme_guid'])
        resume = ProfileResume.objects.get(id=request.POST['resume_id'])
        employer_job = EmployerJob.objects.get(id=request.POST['employer_job_id'])

        if sme.employer_user.employer_id != employer_job.employer_id:
            return HttpResponse("false")

        ec = add_candidate_to_job(resume.profile_id, employer_job.id, sme.employer_user)
        if contact_candidate(ec):
            return HttpResponse('true')
        else:
            return HttpResponse('false')


class SMEJobDropdownView(View):
    def post(self, request):
        sme = SME.objects.get(guid=request.POST['sme_guid'])
        assert sme.employer_user is not None

        context = {"form": SMEContactForm(sme.employer_user.employer)}
        return render(request, "pages/sme_job_dropdown.html", context)


class LoadContactMessage(View):
    def post(self, request):
        sme = SME.objects.get(guid=request.POST['sme_guid'])
        assert sme.employer_user is not None

        employer_job_id = request.POST['employer_job_id']
        if employer_job_id:
            employer_job = EmployerJob.objects.get(id=employer_job_id)
            assert employer_job.employer_id == sme.employer_user.employer_id
            message = employer_job.custom_email_body or get_default_email_body(employer_job)
        else:
            message = ""

        return HttpResponse(message,
                            content_type="text/html")


def search_for_already_contacted_candidate(employer, profile):
    return (EmployerCandidate.objects
                             .filter(employer_job__employer=employer,
                                     profile=profile,
                                     contacted=True)
                             .order_by('contacted_date')
                             .first())


class SMEMonthlyTallyView(View):
    def get(self, request):
        context = {}
        guid = request.GET.get('token')

        if guid:
            context['display_date'] = timezone.now().isoformat().replace("T", " ")[:19]
            context['sme_email'] = SME.objects.get(guid=guid).email

            sme_tallies, qa_tallies, month_names = get_resume_reviews_for_sme_by_month(guid)
            smes = make_id_map(SME, sme_tallies.keys(), ['job'])
            qa_jobs = make_id_map(Job, qa_tallies.keys())

            context['sme_tallies'] = [{"sme": smes[sme_id],
                                       "numbers_of_reviews": numbers}
                                      for (sme_id, numbers) in sme_tallies.items()]
            context['qa_tallies'] = [{"job": qa_jobs[job_id],
                                      "numbers_of_reviews": numbers}
                                     for (job_id, numbers) in qa_tallies.items()]
            context['month_names'] = month_names

            # calculate total by month
            context['total_reviews_by_month'] = total_reviews_by_month = [0] * len(month_names)
            for row in context['sme_tallies']:
                for idx, number in enumerate(row['numbers_of_reviews']):
                    total_reviews_by_month[idx] += number
            for row in context['qa_tallies']:
                for idx, number in enumerate(row['numbers_of_reviews']):
                    total_reviews_by_month[idx] += number
        else:
            context['error'] = "No token was given."

        return render(request, "pages/sme_tallies.html", context)


def make_id_map(model, ids, related=None):
    if related is None:
        related = []

    queryset = model.objects.filter(id__in=ids).select_related(*related)
    return {obj.id: obj for obj in queryset}

