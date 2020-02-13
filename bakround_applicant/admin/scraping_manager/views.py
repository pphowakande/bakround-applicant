__author__ = 'natesymer'

import json

from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import ScraperJobForm, ScraperLoginForm
from bakround_applicant.all_models.db import ScraperJob, ScraperLogin, ProfileResume
from bakround_applicant.services.queue import QueueConnection, QueueNames

class ScrapingIndexView(View):
    def get(self, request):
        scraper_jobs = ScraperJob.objects.filter().order_by('-id')

        is_paginated = not request.GET.get('depaginate')

        if is_paginated:
            page = request.GET.get('page', 1)

            paginator = Paginator(scraper_jobs, 10)
            try:
                scraper_jobs = paginator.page(page)
            except PageNotAnInteger:
                scraper_jobs = paginator.page(1)
            except EmptyPage:
                scraper_jobs = paginator.page(paginator.num_pages)

        return render(request, 'admin/scraping_manager/index.html', {
            'scraper_jobs': scraper_jobs,
            'paginated': is_paginated
        })

class ScrapingStartStopJobView(View):
    def get(self, request, scraper_job_id):
        scraper_job = ScraperJob.objects.get(id=int(scraper_job_id))
        if not scraper_job.running:
            scraper_job.running = True
            scraper_job.save()
            QueueConnection.quick_publish(QueueNames.scraping_service, json.dumps({ "scraper_job_id": scraper_job_id }))
            messages.success(request, 'Started scraping ScraperJob id {} starting at resume #{}.'.format(scraper_job.id, scraper_job.start_offset))
        else:
            scraper_job.running = False
            scraper_job.save()
            messages.success(request, 'Stopped scraping ScraperJob id {}. Will pick up where left off if restarted.'.format(scraper_job.id))
        return redirect('scraping_manager:index')

class ScrapingResetJobView(View):
    def get(self, request, scraper_job_id):
        scraper_job = ScraperJob.objects.get(id=int(scraper_job_id))
        scraper_job.start_offset = 0
        scraper_job.save()
        messages.success(request, "Successfully, (re)started ScraperJob id {} at the beginning.".format(scraper_job_id))
        return redirect('scraping_manager:index')

class ScrapingStopAllJobsView(View):
    def get(self, request):
        QueueConnection().purge(QueueNames.scraping_service)
        ScraperJob.objects.all().update(running=False)
        messages.success(request, "Stopped all ScraperJobs.")
        return redirect('scraping_manager:index')

class ScrapingRequeueAllRunningJobsView(View):
    def get(self, request):
        QueueConnection().purge(QueueNames.scraping_service)
        for scraper_job_id in ScraperJob.objects.filter(running=True).values_list("id", flat=True):
            QueueConnection.quick_publish(QueueNames.scraping_service, json.dumps({ "scraper_job_id": scraper_job_id }))

        messages.success(request, "ScraperJob queue successfully re-built.")
        return redirect("scraping_manager:index")

class ScrapingAddJobView(View):
    def get(self, request):
        return render(request, 'admin/scraping_manager/add_edit.html', {
            'form': ScraperJobForm(),
            'mode': 'add'
        })

    def post(self, request):
        form = ScraperJobForm(request.POST)
        if form.is_valid():
            scraper_job = ScraperJob()
            scraper_job.start_url = form.cleaned_data['start_url']
            scraper_job.job_id = form.cleaned_data['job']
            scraper_job.save()

            QueueConnection.quick_publish(QueueNames.scraping_service, json.dumps({ "scraper_job_id": scraper_job.id }))

            messages.success(request, 'Queued ScraperJob {}.'.format(scraper_job))
        else:
            messages.error(request, 'Please fix the validation errors and try again.')

        return redirect('scraping_manager:index')


class ScrapingEditJobView(View):
    def get(self, request, scraper_job_id):
        scraper_job = ScraperJob.objects.get(pk=scraper_job_id)

        form = ScraperJobForm(initial={
            'start_url': scraper_job.start_url,
            'job': scraper_job.job_id
        })

        return render(request, 'admin/scraping_manager/add_edit.html', {
            'form': form,
            'mode': 'edit',
            'scraper_job_id': scraper_job_id
        })

    def post(self, request, scraper_job_id):
        form = ScraperJobForm(request.POST)
        if form.is_valid():
            scraper_job = ScraperJob.objects.get(pk=scraper_job_id)
            scraper_job.start_url = form.cleaned_data['start_url']
            scraper_job.job_id = form.cleaned_data['job']
            scraper_job.save()

            messages.success(request, 'Scraping job updated successfully.')
        else:
            messages.error(request, 'Please fix the validation errors and try again.')
            return

        return redirect('scraping_manager:index')

def error_message(form, base_message = "Please fix the validation errors and try again:"):
    message = base_message
    for key, value in form.errors.items:
        message += '\n{}: {}'.format(form.fields[key].label, value)
    return message

class ScraperLoginsIndex(View):
    def get(self, request):
        scraper_logins = ScraperLogin.objects.filter().order_by('-id')

        return render(request, 'admin/scraping_manager/logins/index.html', {
            'scraper_logins': scraper_logins
        })

class ScraperLoginsToggleEnabledView(View):
    def get(self, request, scraper_login_id):
        scraper_login = ScraperLogin.objects.filter(id=scraper_login_id).first()
        if not scraper_login:
            messages.error(request, 'No such ScraperLogin.')
            return redirect('scraping_manager:logins_index')
        scraper_login.enabled = not scraper_login.enabled
        scraper_login.save()
        messages.success(request, 'ScraperLogin {} was {}abled.'.format(scraper_login.user_name, "en" if scraper_login.enabled else "dis"))
        return redirect('scraping_manager:logins_index')

class ScraperLoginsAdd(View):
    def get(self, request):
        return render(request, 'admin/scraping_manager/logins/add_edit.html', {
            'form': ScraperLoginForm(),
            'mode': 'add'
        })

    def post(self, request):
        form = ScraperLoginForm(request.POST)
        if form.is_valid():
            ScraperLogin(
                user_name = form.cleaned_data['user_name'],
                password = form.cleaned_data['password'],
                source = form.cleaned_data['source']
            ).save()

            messages.success(request, 'Successfully Created ScraperLogin.')
        else:
            messages.error(request, error_message(form.errors))

        return redirect('scraping_manager:logins_index')

class ScraperLoginsEdit(View):
    def get(self, request, scraper_login_id):
        scraper_login = ScraperLogin.objects.get(pk=scraper_login_id)

        form = ScraperLoginForm(initial={
            'user_name': scraper_login.user_name,
            'password': scraper_login.password,
            'source': scraper_login.source
        })

        return render(request, 'admin/scraping_manager/logins/add_edit.html', {
            'form': form,
            'mode': 'edit',
            'scraper_login_id': scraper_login_id
        })

    def post(self, request, scraper_login_id):
        form = ScraperLoginForm(request.POST)
        if form.is_valid():
            scraper_login = ScraperLogin.objects.get(id=scraper_login_id)
            scraper_login.user_name = form.cleaned_data['user_name']
            scraper_login.password = form.cleaned_data['password']
            scraper_login.source = form.cleaned_data['source']
            scraper_login.save()
            messages.success(request, 'ScraperLogin updated successfully.')
            return redirect('scraping_manager:logins_index')

        messages.error(request, error_message(form))
        return redirect('scraping_manager:logins_index')
