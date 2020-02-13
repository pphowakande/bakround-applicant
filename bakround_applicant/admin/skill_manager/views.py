

from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from bakround_applicant.all_models.db import Skill, Certification


class SkillIndexView(View):
    def get(self, request):
        skills = Skill.objects.all().only('id', 'skill_name').order_by('skill_name')
        context = {'objects': skills, 'object_type': 'skill'}

        for key in ['object_was_added', 'object_was_not_added']:
            if request.session.get(key):
                context[key] = True
                request.session[key] = None

        return render(request, "admin/skill_manager/index.html", context)


class CertIndexView(View):
    def get(self, request):
        certs = Certification.objects.all().only('id', 'certification_name').order_by('certification_name')
        context = {'objects': certs, 'object_type': 'certification'}

        for key in ['object_was_added', 'object_was_not_added']:
            if request.session.get(key):
                context[key] = True
                request.session[key] = None

        return render(request, "admin/skill_manager/index.html", context)


class AddObjectView(View):
    def post(self, request):
        object_type = request.POST['object_type']
        name = request.POST['new_object_name']

        if object_type == 'skill':
            name = name.strip().upper()
            if name and not Skill.objects.filter(skill_name__iexact=name).exists():
                Skill(skill_name=name).save()
                request.session['object_was_added'] = True
            else:
                request.session['object_was_not_added'] = True
        elif object_type == 'certification':
            name = name.strip()
            if name and not Certification.objects.filter(certification_name__iexact=name).exists():
                Certification(certification_name=name).save()
                request.session['object_was_added'] = True
            else:
                request.session['object_was_not_added'] = True
        else:
            raise Exception("unknown object type")

        return redirect('{}_manager:index'.format(object_type))
