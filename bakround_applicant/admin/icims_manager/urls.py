__author__ = 'ajaynayak'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.RankingIndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^(?i)add',
        view=staff_member_required(views.RankingAddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^(?i)start_stop/(?P<ranking_job_id>\d+)',
        view=staff_member_required(views.RankingStartStopJobView.as_view()),
        name='complete_job'
    ),
]
