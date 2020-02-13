__author__ = 'ajaynayak'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.ScrapingIndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^(?i)add',
        view=staff_member_required(views.ScrapingAddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^(?i)requeue_all',
        view=staff_member_required(views.ScrapingRequeueAllRunningJobsView.as_view()),
        name='requeue_running'
    ),
    url(
        regex=r'^(?i)stop_all',
        view=staff_member_required(views.ScrapingStopAllJobsView.as_view()),
        name='stop_all_jobs'
    ),
    url(
        regex=r'^(?i)reset/(?P<scraper_job_id>\d+)',
        view=staff_member_required(views.ScrapingResetJobView.as_view()),
        name='reset_job'
    ),
    url(
        regex=r'^(?i)edit/(?P<scraper_job_id>\d+)',
        view=staff_member_required(views.ScrapingEditJobView.as_view()),
        name='edit_job'
    ),
    url(
        regex=r'^(?i)start_stop/(?P<scraper_job_id>\d+)',
        view=staff_member_required(views.ScrapingStartStopJobView.as_view()),
        name='complete_job'
    ),
    url(
        regex=r'^(?i)logins/edit/(?P<scraper_login_id>\d+)/toggle',
        view=staff_member_required(views.ScraperLoginsToggleEnabledView.as_view()),
        name='toggle_enabled_scraper_login'
    ),
    url(
        regex=r'^(?i)logins/edit/(?P<scraper_login_id>\d+)',
        view=staff_member_required(views.ScraperLoginsEdit.as_view()),
        name='edit_scraper_login'
    ),
    url(
        regex=r'^(?i)logins/add',
        view=staff_member_required(views.ScraperLoginsAdd.as_view()),
        name='add_scraper_login'
    ),
    url(
        regex=r'^(?i)logins',
        view=staff_member_required(views.ScraperLoginsIndex.as_view()),
        name='logins_index'
    ),
]
