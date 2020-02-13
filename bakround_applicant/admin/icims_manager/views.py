__author__ = 'poonam'

import json

from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime

from .forms import RankingJobForm
from bakround_applicant.all_models.db import RankingJob, ProfileResume
from bakround_applicant.services.queue import QueueConnection, QueueNames

class RankingIndexView(View):
    def get(self, request):
        ranking_jobs = RankingJob.objects.filter().order_by('-id')

        is_paginated = not request.GET.get('depaginate')

        if is_paginated:
            page = request.GET.get('page', 1)

            paginator = Paginator(ranking_jobs, 10)
            try:
                ranking_jobs = paginator.page(page)
            except PageNotAnInteger:
                ranking_jobs = paginator.page(1)
            except EmptyPage:
                ranking_jobs = paginator.page(paginator.num_pages)

        return render(request, 'admin/icims_manager/index.html', {
            'ranking_jobs': ranking_jobs,
            'paginated': is_paginated
        })


class RankingAddJobView(View):
    def get(self, request):
        return render(request, 'admin/icims_manager/add_edit.html', {
            'form': RankingJobForm(),
            'mode': 'add'
        })

    def post(self, request):
        form = RankingJobForm(request.POST)
        if form.is_valid():
            ranking_job = RankingJob()
            ranking_job.start_date = datetime.datetime.today().strftime('%Y-%m-%d')
            ranking_job.save()
            QueueConnection.quick_publish(QueueNames.icims_service, json.dumps({ "ranking_job_id": ranking_job.id }))
            messages.success(request, 'Queued RankingJob {}.'.format(ranking_job))
        else:
            messages.error(request, 'Please fix the validation errors and try again.')

        return redirect('icims_manager:index')


class RankingStartStopJobView(View):
    def get(self, request, ranking_job_id):
        ranking_job = RankingJob.objects.get(id=int(ranking_job_id))
        if not ranking_job.running:
            ranking_job.running = True
            ranking_job.save()
            QueueConnection.quick_publish(QueueNames.icims_service, json.dumps({ "ranking_job_id": ranking_job_id }))
            messages.success(request, 'Started scraping RankingJob')
        else:
            ranking_job.running = False
            ranking_job.save()
            messages.success(request, 'Stopped scraping RankingJob id {}. Will pick up where left off if restarted.'.format(ranking_job.id))
        return redirect('icims_manager:index')

def error_message(form, base_message = "Please fix the validation errors and try again:"):
    message = base_message
    for key, value in form.errors.items:
        message += '\n{}: {}'.format(form.fields[key].label, value)
    return message
