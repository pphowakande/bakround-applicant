__author__ = 'tplick'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views
from django.contrib.admin.views.decorators import staff_member_required


urlpatterns = [
    url(
        regex=r'^test_scoring/?$',
        view=staff_member_required(views.TestScoringView.as_view()),
        name='test_scoring'
    ),

    url(
        regex=r'^scheduler_tool/?$',
        view=staff_member_required(views.SchedulerView.as_view()),
        name='scheduler_tool',
    ),
]
