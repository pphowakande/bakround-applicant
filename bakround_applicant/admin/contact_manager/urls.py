__author__ = 'tplick'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.IndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^employer/(?P<employer_id>\d+)$',
        view=staff_member_required(views.EmployerView.as_view()),
        name='employer',
    ),
    url(
        regex=r'^mark_as_contacted/(?P<candidate_id>\d+)$',
        view=staff_member_required(views.MarkAsContactedView.as_view()),
        name='mark_as_contacted',
    ),
]
