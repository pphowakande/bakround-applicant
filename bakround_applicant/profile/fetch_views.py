__author__ = "tplick"  # May 11, 2017

from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from bakround_applicant.all_models.db import Skill, Certification

class FetchSkillsView(LoginRequiredMixin, View):
    def get(self, request):
        skills = Skill.objects.order_by('id').values('id', 'skill_name')
        return HttpResponse(json.dumps(({"skills": list(skills)})), content_type="application/json")

class FetchCertsView(LoginRequiredMixin, View):
    def get(self, request):
        certs = Certification.objects.order_by('id').values('id', 'certification_name')
        return HttpResponse(json.dumps({"certs": list(certs)}), content_type="application/json")

