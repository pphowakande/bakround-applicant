__author__ = 'ajaynayak'

# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.SMEList.as_view()),
        name='index'
    ),
    url(
        regex=r'^(?i)edit/(?P<sme_id>\d+)$',
        view=staff_member_required(views.SMEEdit.as_view()),
        name='edit_sme'
    ),
    url(
        regex=r'^(?i)create$',
        view=staff_member_required(views.SMECreate.as_view()),
        name='create_sme'
    ),
    url(
        regex=r'^(?i)delete/(?P<sme_id>\d+)$',
        view=staff_member_required(views.SMEDelete.as_view()),
        name='delete_sme'
    ),

    url(
        regex=r'^(?i)edit_region/(?P<region_id>\d+)$',
        view=staff_member_required(views.RegionEdit.as_view()),
        name='edit_region'
    ),
    url(
        regex=r'^(?i)create_region$',
        view=staff_member_required(views.RegionCreate.as_view()),
        name='create_region'
    ),
    url(
        regex=r'^does_city_exist$',
        view=staff_member_required(views.DoesCityExistView.as_view()),
        name='does_city_exist',
    ),
]
