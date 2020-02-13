__author__ = 'ajaynayak'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.Index.as_view()),
        name='index'
    ),
    url(
        regex=r'^(?i)editjob/(?P<job_id>\d+)/$',
        view=staff_member_required(views.EditJob.as_view()),
        name='edit_job'
    ),
    url(
        regex=r'^add_job/$',
        view=staff_member_required(views.AddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^delete_job/$',
        view=staff_member_required(views.DeleteJobView.as_view()),
        name='delete_job'
    ),
    url(
        regex=r'^rescore_profiles/$',
        view=staff_member_required(views.RescoreProfilesView.as_view()),
        name='rescore_profiles'
    ),

    # added by tplick on 20 Sept 2017
    url(
        regex=r'^rescore_job_family/$',
        view=staff_member_required(views.RescoreJobFamilyView.as_view()),
        name='rescore_job_family',
    ),
]
