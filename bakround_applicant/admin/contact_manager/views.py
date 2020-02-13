__author__ = "tplick"

import logging
import uuid
from datetime import datetime
from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from bakround_applicant.all_models.db import Employer, EmployerCandidate, EmployerJob, EmployerCandidateResponse,\
                                                EmployerJobUser, Profile, ProfileResume
from django.utils import timezone
from django.db.models import F
from bakround_applicant.services.notificationservice import util

from ..stats_manager.views import get_recruiter_lists_for_jobs_of_employer, show_recruiters


class IndexView(View):
    def get(self, request):
        employers = (Employer.objects
                             .filter(external_contacting_enabled=True)
                             .order_by('company_name'))

        context = {"employers": employers}
        return render(request, "admin/contact_manager/index.html", context)


class EmployerView(View):
    def get(self, request, employer_id):
        employer = Employer.objects.get(id=employer_id)
        candidates = get_candidates_for_employer(employer)
        recruiters = get_recruiter_lists_for_jobs_of_employer(employer)

        context = {
            "employer": employer,
            "candidates": candidates,
            "recruiter_names_by_job": {id: show_recruiters(names) for (id, names) in recruiters.items()}
        }
        return render(request, "admin/contact_manager/employer.html", context)


def get_candidates_for_employer(employer):
    candidates = (EmployerCandidate.objects
                                   .filter(employer_job__employer=employer, employer_job__open=True)
                                   .order_by('employer_job__job_name',
                                             'employer_job__city',
                                             'employer_job__state__state_code',
                                             '-contacted_date')
                                   .select_related('profile',
                                                   'employer_job')
                                   .extra(select={"resume_url": "profile_resume.url"},
                                          tables=[
                                              "profile_resume"
                                          ],
                                          where=
    ["""
         profile_resume.profile_id = profile.id
         AND
         profile_resume.id in
            (select distinct on (profile_id)
                id
                from profile_resume
                order by profile_id, id desc)
     """,

     """
         employer_candidate.contacted = TRUE and
             employer_candidate.responded = FALSE and
             employer_candidate.contacted_externally = FALSE
         and (employer_candidate.notification_id is NULL
                or employer_candidate.notification_id in (select id from notification where sent = FALSE)
                or employer_candidate.notification_id not in
                    (select distinct n1.id
                        from notification_recipient_event nre
                        join notification_recipient nr on nr.id = nre.notification_recipient_id
                        join notification n1 on n1.id = nr.notification_id
                        where nre.action = 'delivered'))
     """]))

    return candidates


class MarkAsContactedView(View):
    def post(self, request, candidate_id):
        candidate = EmployerCandidate.objects.get(id=candidate_id)
        candidate.contacted_externally = True
        candidate.save()

        return HttpResponse("ok")
