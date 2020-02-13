# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required

from bakround_applicant.users import views
import bakround_applicant.admin.views as admin_views
from bakround_applicant.employer import views as employer_views

# TODO: ensure migrations in Prod will be fine with the resumes app being renamed sme_feedback

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^about/$', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    url(r'^legal/$', TemplateView.as_view(template_name='pages/user_agreement.html'), name='legal'),
    url(r'^profile/', include('bakround_applicant.profile.urls', namespace='profile')),
    url(r'^employer/', include('bakround_applicant.employer.urls', namespace='employer')),
    url(r'^icims/', include('bakround_applicant.icims.urls', namespace='icims')),
    url(r'^users/', include('bakround_applicant.users.urls', namespace='users')),
    url(r'^webhooks/', include('bakround_applicant.webhooks.urls', namespace='webhooks')),
    url(r'^accounts/login/', views.SignInView.as_view(), name='account_login'),
    url(r'^accounts/signup/employer/?$', employer_views.EmployerSignupView.as_view(), name='employer_signup'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^sme_feedback/', include('bakround_applicant.sme_feedback.urls', namespace='sme_feedback')),
    url(r'^stats/', include('bakround_applicant.stats.urls', namespace='stats')),

    url( # Account Settings page
        r'^settings/',
        views.AccountSettingsView.as_view(),
        name='account_settings'
    ),

    # Candidate Email endpoints. Should be rolled into the employer app.

    url(
        regex=r'^candidate/accept/(?P<employer_candidate_guid>[-a-f\d]+)/?$',
        view=views.CandidateAcceptView.as_view(),
        name='candidate_accept_interes',
    ),

    url(
        regex=r'^candidate/decline/(?P<employer_candidate_guid>[-a-f\d]+)/?$',
        view=views.CandidateDeclineView.as_view(),
        name='candidate_decline_interest',
    ),

    url(
        regex=r'^candidate/decline_reason/(?P<employer_candidate_guid>[-a-f\d]+)/?$',
        view=views.CandidateDeclineReasonView.as_view(),
        name='candidate_decline_reason',
    ),

    url(
        regex=r'^candidate/send_message/?$',
        view=views.CandidateSendMessageView.as_view(),
        name='candidate_send_message',
    ),

    url(
        regex=r'^unsubscribe/(?P<employer_candidate_guid>[-a-f\d]+)/?$',
        view=views.UnsubscribeView.as_view(),
        name='unsubscribe',
    ),

    url(
        regex=r'^company_website_redirect/(?P<employer_candidate_guid>[-a-f\d]+)$',
        view=views.CandidateRecordClickView.as_view(),
        name='company_website_redirect',
    ),

    # Auth Token Code

    url(
        regex=r'^initial_login/(?P<token>[-a-f\d]+)/?',
        view=views.TokenLoginView.as_view(),
        name='initial_token_login',
    ),

    url(
        regex=r'^set_initial_password/?$',
        view=login_required(views.SetPasswordAfterTokenLoginView.as_view()),
        name='set_initial_password',
    ),

    # Admin

    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, admin.site.urls),
    url(r'^staff/', include('bakround_applicant.admin.urls', namespace='staff')),

    url(
        r'^job_manager/',
        include('bakround_applicant.admin.job_manager.urls', namespace='job_manager')
    ),

    url( # Clear Cache
        r'^admin/clear_cache/$',
        staff_member_required(admin_views.ClearCacheView.as_view()),
        name='clear_cache'
    ),

    url( # SME Management UI
        r'^sme_manager/',
        include('bakround_applicant.admin.sme_manager.urls', namespace='sme_manager')
    ),

    url( # Profile Remapper UI
        r'^profile_remap_manager/',
        include('bakround_applicant.admin.profile_remap_manager.urls', namespace='profile_remap_manager')
    ),

    url(
        r'^stats_manager/',
        include('bakround_applicant.admin.stats_manager.urls', namespace='stats_manager')
    ),

    url( # This is actually called "Profile Search" in Settings.
        r'^profile_manager/',
        include('bakround_applicant.admin.profile_manager.urls', namespace='profile_manager')
    ),

    url(
        r'^scraping_manager/',
        include('bakround_applicant.admin.scraping_manager.urls', namespace='scraping_manager')
    ),

    url(
        r'^icims_manager/',
        include('bakround_applicant.admin.icims_manager.urls', namespace='icims_manager')
    ),

    url(
        r'^manual_verifier/',
        include('bakround_applicant.admin.manual_verifier.urls', namespace='manual_verifier')
    ),

    url(
        r'^skill_manager/',
        include('bakround_applicant.admin.skill_manager.urls', namespace='skill_manager')
    ),
    url(
        r'^cert_manager/',
        include('bakround_applicant.admin.cert_manager.urls', namespace='certification_manager')
    ),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        url(r'^403/$', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        url(r'^404/$', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        url(r'^500/$', default_views.server_error),
    ]
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
