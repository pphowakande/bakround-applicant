# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        regex=r'^search$',
        view=views.SearchView.as_view(),
        name='search'
    ),
    url(
        regex=r'^icims_search$',
        view=views.IcimsSearchView.as_view(),
        name='icims_search'
    ),
    url(
        regex=r'representation/(\d+)(?:.html|/)?$',
        view=views.HTMLDetailView.as_view(),
        name='html'
    ),
    url(
        regex=r'representation/(\d+).json$',
        view=views.JSONDetailView.as_view(),
        name='json'
    ),
    url(
        # backwards compat
        regex=r'^(?:representation|pdf)/(\d+)(?:.pdf|/)$',
        view=views.PDFDetailView.as_view(),
        name='pdf'
    ),
    url(
        # backwards compat
        regex=r'^(?:representation|pdf)/icims/(\d+)(?:.pdf|/)$',
        view=views.IcimsPDFDetailView.as_view(),
        name='pdf'
    )
]
