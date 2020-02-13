# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.SMEFeedbackIndexView.as_view(),
        name='sme_feedback'
    ),
    url(
        regex=r'^open_resume',
        view=views.SMEOpenResumeView.as_view(),
        name='open_resume'
    ),
    url(
        regex=r'^do_not_ask_again$',
        view=views.SMEDoNotAskAgainView.as_view(),
        name='do_not_ask_again',
    ),
    url(
        regex=r'^view_resume/(?P<resume_id>\d+)/?$',
        view=views.ViewResumeView.as_view(),
        name='view_resume',
    ),
    url(
        regex=r'^sme_contact_candidate$',
        view=views.SMEContactCandidate.as_view(),
        name='sme_contact_candidate',
    ),
    url(
        regex=r'^job_dropdown$',
        view=views.SMEJobDropdownView.as_view(),
        name='job_dropdown',
    ),
    url(
        regex=r'^load_contact_message$',
        view=views.LoadContactMessage.as_view(),
        name='load_contact_message',
    ),

    # added by tplick, 26 March 2018
    url(
        regex=r'^tallies$',
        view=views.SMEMonthlyTallyView.as_view(),
        name='tallies',
    ),
]
