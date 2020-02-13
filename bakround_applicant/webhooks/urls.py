__author__ = 'ajaynayak'

# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^(?i)handle_email_event$',
        view=views.HandleEmailEvent.as_view(),
        name='handle_email_event'
    )
]
