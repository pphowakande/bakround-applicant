__author__ = "tplick"

import django
from django.views import View
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from django.db.models import Count, F
from bakround_applicant.all_models.db import Job, Skill, JobSkill, \
                                             Profile, Certification, \
                                             JobCertification, JobFamily, SMEFeedback, \
                                             BgPositionMaster, IndustryJobFamily
from ...services.queue import QueueNames, QueueConnection
import json

import random
import string

from django.urls import reverse
from django.http import HttpResponse

from django.db.models import Max
from django.db import transaction

from . import utils
from .utils import perform_remap_to_job
from django.contrib import messages


class IndexView(View):
    def get(self, request):
        context = {}

        context['jobs_with'] = (Job.objects
                                   .filter(employer_id__isnull=True, remap_order__isnull=False)
                                   .order_by('remap_order', 'id'))

        context['jobs_without'] = (Job.objects
                                      .filter(employer_id__isnull=True, remap_order=None)
                                      .order_by('job_name'))

        context['counts'] = utils.get_counts()

        max_order = Job.objects.all().aggregate(Max('remap_order'))
        context['all_orders'] = range(1, (max_order['remap_order__max'] or 0) + 2)

        return render(request, "admin/profile_remap_manager/index.html", context)


class AddJobView(View):
    def post(self, request):
        max_order = Job.objects.all().aggregate(Max('remap_order'))

        job = Job.objects.get(id=request.POST['job_id'])
        job.remap_order = (max_order['remap_order__max'] or 0) + 1
        job.save()

        return redirect('profile_remap_manager:index')


class RemoveJobView(View):
    def post(self, request, job_id):
        job = Job.objects.get(id=job_id)
        job.remap_order = None
        job.save()

        return redirect('profile_remap_manager:index')


class EditJobView(View):
    def get(self, request, job_id):
        context = {}

        job = Job.objects.get(id=job_id)
        context['job'] = job

        return render(request, "admin/profile_remap_manager/edit_job.html", context)

    def post(self, request, job_id):
        job = Job.objects.get(id=job_id)
        job.remap_query = request.POST['query']
        job.save()

        return redirect('profile_remap_manager:index')


class CleanUpOrderView(View):
    def post(self, request):
        clean_up_remap_order()
        return redirect('profile_remap_manager:index')


def clean_up_remap_order():
    with transaction.atomic():
        for idx, job in enumerate(Job.objects
                                     .filter(employer_id__isnull=True, remap_order__isnull=False)
                                     .order_by('remap_order', 'id')):
            if job.remap_order != idx + 1:
                job.remap_order = idx + 1
                job.save(update_fields=["remap_order"])


class ChangeOrderView(View):
    def post(self, request, job_id):
        new_order = int(request.POST['new_order'])
        (Job.objects
            .filter(remap_order__gte=new_order)
            .update(remap_order=F('remap_order')+1))
        (Job.objects
            .filter(id=job_id)
            .update(remap_order=new_order))
        return redirect('profile_remap_manager:index')


class RemapJobNowView(View):
    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
            if job.remap_query:
                perform_remap_to_job(job)
                messages.success(request,
                                 "Job #{} has been remapped.".format(job_id))
            else:
                messages.error(request,
                               "The remap query for job #{} is blank.".format(job_id))
        except Exception as e:
            messages.error(request,
                           "There was an error while remapping job #{}.".format(job_id))
            utils.logger.exception(e)
        return redirect('profile_remap_manager:index')

