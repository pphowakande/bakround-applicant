__author__ = 'natesymer'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.VerifierIndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^(?i)requests/verify',
        view=staff_member_required(views.VerifyView.as_view()),
        name='verify'
    ),
    url(
        regex=r'^(?i)profiles/update',
        view=staff_member_required(views.VerifierUpdateProfileView.as_view()),
        name='update_profile'
    ),
    url(
        regex=r'^(?i)requests/update_status',
        view=staff_member_required(views.VerifierUpdateStatusView.as_view()),
        name='update_status'
    ),
    url(
        regex=r'^(?i)requests',
        view=staff_member_required(views.VerifierRequestsView.as_view()),
        name='verifier_requests_view'
    )
]

