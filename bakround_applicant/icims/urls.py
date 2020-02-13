# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from . import views
from ..utilities.functions import employer_flag_required, employer_owner_required
from . import closeability_metric
from django.contrib.admin.views.decorators import staff_member_required


urlpatterns = [
    url(
        regex=r'^$',
        view=employer_flag_required(views.IcimsIndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^jobs',
        view=employer_flag_required(views.IcimsJobsView.as_view()),
        name='jobs'
    ),
    url(
        regex=r'^search/(?P<icims_job_id>\d+)',
        view=employer_flag_required(views.ProfileSearchView.as_view()),
        name='search'
    ),
    url(
        regex=r'^profile_summary/(?P<profile_id>\d+)',
        view=employer_flag_required(views.ProfileSummaryView.as_view()),
        name='ProfileSummaryView'
    ),
    url(
        regex=r'^add_job',
        view=employer_flag_required(views.IcimsAddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^job/(?P<icims_job_id>\d+)/candidates_list',
        view=employer_flag_required(views.IcimsJobCandidatesListView.as_view()),
        name='job_candidates_list'
    ),
    url(
        regex=r'^job/(?P<icims_job_id>\d+)',
        view=employer_flag_required(views.IcimsJobDetailView.as_view()),
        name='job'
    ),
    url(
        regex=r'^csv_export/(?P<icims_job_id>\d+)$',
        view=views.ExportCandidatesView.as_view(),
        name='csv_export'
    ),

    url(
        regex=r'^stats$',
        view=views.IcimsStatsView.as_view(),
        name='stats',
    ),

    # added by nsymer on 30 Sept 2018
    url(
        regex=r'^contact_info/(?P<candidate_id>\d+)$',
        view=views.CandidateContactView.as_view(),
        name='contact_info'
    ),

    # added by natesymer on 11.14.18
    url(
        regex=r'^preview_intro/(?P<icims_job_id>\d+)$',
        view=views.IcimsPreviewCandidateContact.as_view(),
        name='preview_intro'
    )
]
