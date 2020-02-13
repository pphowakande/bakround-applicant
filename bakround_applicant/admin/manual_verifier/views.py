__author__ = "natesymer"

import re
import json

from django.db.models import Subquery, OuterRef
from django.http import HttpResponse
from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from bakround_applicant.all_models.db import ProfileVerificationRequest, ProfileResume, ProfileEmail, ProfileResume, Profile, ProfilePhoneNumber, EmployerCandidate, EmployerJob
from bakround_applicant.services.queue import QueueConnection
from bakround_applicant.services.verifyingservice.util import add_contact, collect_contact_info_for_profile
from bakround_applicant.services.verifyingservice.consumer import lookup_profile
from . import forms

from bakround_applicant.utilities.functions import get_website_root_url, json_result, make_job_structure_for_dropdown, \
                                                   make_choice_set_for_state_codes, get_job_families_for_employer, json_result, employer_flag_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .utils import JSONView, profile_to_json, pvr_to_status_json, vector_diff_param_update_model, profile_from_params

class VerifierIndexView(View):
    """HTML page that serves the Manual Verifier React app."""
    def get(self, request):
        context = {
            'props': json.dumps({})
        }

        return render(request, "admin/manual_verifier/index.html", context)

class VerifierRequestsView(LoginRequiredMixin, JSONView):
    """POST/GET all verification requests."""
    def go(self, request, params):
        page = params.get("page", 0)
        page_size = params.get("page_size", 20)

        requests = ProfileVerificationRequest.objects.filter(verified=False, metadata__bkrnd_ecid__isnull=False)

        fltr = params.get("filter", 'all')
        if fltr == "contacted":
            requests = requests.filter(contacted=True, responded=False)
        elif fltr == "not_contacted":
            requests = requests.filter(contacted=False)
        elif fltr == "responded":
            requests = requests.filter(contacted=True, responded=True)
        elif fltr == "pending_action":
            requests = requests.filter(pending_action=True)
        elif fltr == "broken":
            requests = requests.filter(broken=True)
        elif fltr == "unreachable":
            requests = requests.filter(unreachable=True)

        url_qs = ProfileResume.objects.filter(profile_id=OuterRef("profile_id")).order_by("-id").values_list("url", flat=True)[:1]
        requests = requests.annotate(resume_url=Subquery(url_qs)).order_by('-id')

        total_requests = requests.count()

        requests = requests[(page * page_size):((page * page_size) + page_size)]

        json_requests = []
        for r in requests:
            collect_contact_info_for_profile(r.profile)

            if 'bkrnd_ecid' in r.metadata:
               ejid = EmployerCandidate.objects.filter(id=int(r.metadata["bkrnd_ecid"])).first()
               if ejid:
                   ejid = ejid.employer_job_id
            else:
               ejid = EmployerCandidate.objects.filter(profile_id=r.profile_id,
                                                                     employer_job_id__isnull=False,
                                                                     employer_job__employer_id__isnull=False,
                                                                     contacted=True).order_by('-id').values_list('employer_job_id', flat=True).first()

            res = {
                "id": r.id,
                "resume_url": r.resume_url,
                "status": pvr_to_status_json(r),
                "profile": profile_to_json(r.profile)
            }

            if ejid:
                ej = EmployerJob.objects.get(id=ejid)
                res["job"] = {
                    'id': ej.id,
                    'title': ej.job_name,
                    'generic_title': ej.job.job_name,
                    'company_name': ej.employer.company_name
                }

            json_requests.append(res)

        count_qs = ProfileVerificationRequest.objects.filter(verified=False)

        return {
            'requests': json_requests,
            'total_requests': total_requests,
            'stats': [
                {
                    'name': 'Unverified',
                    'value': count_qs.count()
                },
                {
                    'name': "Contacted",
                    'value': count_qs.filter(contacted=True).count()
                },
                {
                    'name': "Not Contacted",
                    'value': count_qs.filter(contacted=False).count()
                },
                {
                    'name': "Broken",
                    'value': count_qs.filter(broken=True).count()
                },
                {
                    'name': "Unreachable",
                    'value': count_qs.filter(unreachable=True).count()
                }
            ]
        }

class VerifierUpdateStatusView(JSONView):
    def go(self, request, params):
        request = ProfileVerificationRequest.objects.filter(id=int(params.get('request_id'))).first()
        if not request:
            return { "error": "Verification request does not exist.", "queued": False }

        if 'contacted' in params:
            request.contacted = params['contacted']

        if 'responded' in params:
            request.responded = params['responded']

        if 'pending_action' in params:
            request.pending_action = params['pending_action']

        if 'broken' in params:
            request.broken = params['broken']

        if 'unreachable' in params:
            request.unreachable = params['unreachable']

        request.save()

        return {"success": True}

class VerifierUpdateProfileView(JSONView):
    def go(self, request, params):
        profile = profile_from_params(params)

        if not profile:
            return { "error": "Profile not found." }

        # Update our profile using our scalar parameters

        updated = False
        for attr in ['first_name', 'middle_name', 'last_name', 'summary', 'street_address']:
            if attr in params:
                setattr(profile, attr, params[attr] or None)
                updated = True

        if updated:
            profile.save()

        # Update our profile using the vector parameters

        vector_diff_param_update_model(ProfilePhoneNumber, profile, params.get("phones", []))
        vector_diff_param_update_model(ProfileEmail, profile, params.get("emails", []))
        return { "success": True }


class VerifyView(JSONView):
    def go(self, request, params):
        request = ProfileVerificationRequest.objects.filter(id=int(params.get('request_id'))).first()
        if not request:
            return { "error": "Verification request does not exist.", "queued": False }

        request.profile.name_verification_completed = True
        request.profile.save()

        request.verified = True
        request.save()

        if request.callback_queue and request.callback_message:
            QueueConnection.quick_publish(queue_name=request.callback_queue, body=request.callback_message)
            return { "queued": True }

        return { "queued": False }


class PerformLookupView(JSONView):
    def go(self, request, params):
        pvr = ProfileVerificationRequest.objects.filter(id=int(params.get('request_id'))).first()
        if not pvr:
            return { "error": "Verification request does not exist." }

        pvr.lookup_performed = True
        pvr.save()

        profile = pvr.profile
        if not profile:
            return { "error": "Profile does not exist." }

        if lookup_profile(profile, require_emails=True, use_cache=False):
            profile.refresh_from_db()
            return { "profile": profile_to_json(profile) }

        return {}
