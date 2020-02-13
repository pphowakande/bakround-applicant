# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from . import views
from ..utilities.functions import employer_flag_required, employer_owner_required
from . import closeability_metric
from django.contrib.admin.views.decorators import staff_member_required


urlpatterns = [
    url(
        regex=r'^$',
        view=employer_flag_required(views.EmployerIndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^jobs',
        view=employer_flag_required(views.EmployerJobsView.as_view()),
        name='jobs'
    ),
    url(
        regex=r'^search/(?P<employer_job_id>\d+)',
        view=employer_flag_required(views.ProfileSearchView.as_view()),
        name='search'
    ),
    url(
        regex=r'^profile_summary/(?P<profile_id>\d+)',
        view=employer_flag_required(views.ProfileSummaryView.as_view()),
        name='ProfileSummaryView'
    ),
    url(
        regex=r'^add_job',
        view=employer_flag_required(views.EmployerAddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^edit_job/(?P<employer_job_id>\d+)',
        view=employer_flag_required(views.EmployerEditJobView.as_view()),
        name='edit_job'
    ),
    url(
        regex=r'^job/(?P<employer_job_id>\d+)/candidates_list',
        view=employer_flag_required(views.EmployerJobCandidatesListView.as_view()),
        name='job_candidates_list'
    ),
    url(
        regex=r'^job/(?P<employer_job_id>\d+)',
        view=employer_flag_required(views.EmployerJobDetailView.as_view()),
        name='job'
    ),
    url(
        regex=r'^add_candidate_to_job',
        view=employer_flag_required(views.AddCandidateToJobView.as_view()),
        name='add_candidate_to_job'
    ),
    url(
        regex=r'^remove_candidate_from_job',
        view=employer_flag_required(views.RemoveCandidateFromJobView.as_view()),
        name='remove_candidate_from_job'
    ),
    url(
        regex=r'^assign_users_to_job/(?P<employer_job_id>\d+)$',
        view=employer_flag_required(views.AssignUsersToJobView.as_view()),
        name='assign_users_to_job'
    ),
    url(
        regex=r'^add_user_to_job$',
        view=employer_flag_required(views.AddUserToJobView.as_view()),
        name='add_user_to_job'
    ),
    url(
        regex=r'^remove_user_from_job$',
        view=employer_flag_required(views.RemoveUserFromJobView.as_view()),
        name='remove_user_from_job'
    ),
    url(
        regex=r'^job_settings/(?P<employer_job_id>\d+)',
        view=employer_flag_required(views.JobSettingsView.as_view()),
        name='job_settings'
    ),
    url(
        regex=r'^csv_export/(?P<employer_job_id>\d+)$',
        view=views.ExportCandidatesView.as_view(),
        name='csv_export'
    ),
    url(
        regex=r'^closeability_metric/?$',
        view=closeability_metric.CloseabilityMetricView.as_view(),
        name='closeability_metric',
    ),

    # tplick 16 June 2017
    url(
        regex=r'^add_user/?$',
        view=employer_owner_required(views.AddUserView.as_view()),
        name='add_employer_user',
    ),

    # tplick 19 June 2017
    url(
        regex=r'^manage_users/?$',
        view=employer_owner_required(views.ManageUserView.as_view()),
        name='manage_employer_users',
    ),
    url(
        regex=r'^edit_user/(?P<employer_user_id>\d+)$',
        view=employer_owner_required(views.EditUserView.as_view()),
        name='edit_employer_user',
    ),
    url(
        regex=r'^resend_login_token/(?P<employer_user_id>\d+)$',
        view=employer_owner_required(views.ResendLoginTokenView.as_view()),
        name='resend_login_token',
    ),
    url(
        regex=r'^delete_user/(?P<employer_user_id>\d+)$',
        view=employer_owner_required(views.DeleteUserView.as_view()),
        name='delete_employer_user',
    ),

    # tplick 19 July 2017
    url(
        regex=r'^custom_job_profiles/?$',
        view=employer_owner_required(views.CustomJobProfileIndexView.as_view()),
        name='custom_job_profile_index',
    ),
    url(
        regex=r'^create_custom_job_profile/?$',
        view=employer_owner_required(views.CreateCustomJobProfileView.as_view()),
        name='custom_job_profile_create',
    ),
    url(
        regex=r'^delete_custom_job_profile/(?P<job_id>\d+)$',
        view=employer_owner_required(views.DeleteCustomJobProfileView.as_view()),
        name='custom_job_profile_delete',
    ),

    # tplick 21 July 2017
    url(
        regex=r'^edit_custom_job_profile/(?P<job_id>\d+)$',
        view=employer_owner_required(views.EditCustomJobProfileView.as_view()),
        name='custom_job_profile_edit',
    ),

    # tplick 26 July 2017
    url(
        regex=r'^modify_custom_job_profile/(?P<job_id>\d+)$',
        view=employer_owner_required(views.ModifyCustomJobProfileView.as_view()),
        name='custom_job_profile_modify',
    ),

    url(
        regex=r'^email_settings/?$',
        view=employer_flag_required(views.EmailSettingsView.as_view()),
        name='email_settings',
    ),
    url(
        regex=r'^email_settings/body/?$',
        view=employer_flag_required(views.EmailSettingsBodyView.as_view()),
        name='email_settings_body',
    ),
    url(
        regex=r'^email_settings/logo/?$',
        view=employer_flag_required(views.EmailSettingsLogoView.as_view()),
        name='email_settings_logo',
    ),

    url(
        regex=r'^send_follow_up_emails/?$',
        view=views.FollowUpView.as_view(),
        name='send_follow_up_emails',
    ),

    url(
        regex=r'^candidate_status/(?P<candidate_id>\d+)$',
        view=employer_flag_required(views.CandidateStatusView.as_view()),
        name='candidate_status',
    ),

    url(
        regex=r'^fetch_possible_statuses/?$',
        view=employer_flag_required(views.FetchPossibleStatusesView.as_view()),
        name='fetch_possible_statuses',
    ),
    url(
        regex=r'^fetch_possible_reject_reasons/?$',
        view=employer_flag_required(views.FetchPossibleRejectReasonsView.as_view()),
        name='fetch_possible_reject_reasons',
    ),
    url(
        regex=r'^change_candidate_status/(?P<candidate_id>\d+)?$',
        view=employer_flag_required(views.ChangeCandidateStatusView.as_view()),
        name='change_candidate_status',
    ),

    url(
        regex=r'^clos_sql/?$',
        view=staff_member_required(closeability_metric.CloseabilityMetricSqlView.as_view()),
        name='closeability_metric_sql',
    ),

    # added by tplick on 25 August 2017
    url(
        regex=r'^dismiss_tour/(?P<tour_name>\w+)$',
        view=employer_flag_required(views.DismissTourView.as_view()),
        name='dismiss_tour',
    ),

    # added by tplick on 18 September 2017

    url(
        regex=r'^candidate_status_detail/(?P<employer_candidate_id>\w+)$',
        view=employer_flag_required(views.EmployerCandidateStatusDetailView.as_view()),
        name='candidate_status_detail',
    ),

    # added by tplick on 20 November 2017
    url(
        regex=r'^restrict_profile/(?P<profile_id>\d+)$',
        view=employer_flag_required(views.RestrictProfileView.as_view()),
        name='restrict_profile',
    ),

    # added by tplick on 15 December 2017
    url(
        regex=r'^submit_feedback_post$',
        view=views.EmployerFeedbackSubmissionView.as_view(),
        name='submit_feedback_post',
    ),

    # added by tplick on 22 January 2018
    url(
        regex=r'^set_autopilot_for_job/(?P<employer_job_id>\d+)$',
        view=views.EnableAutopilotView.as_view(),
        name='set_autopilot_for_job',
    ),

    # added by tplick on 30 January 2018
    url(
        regex=r'^notification_settings$',
        view=views.NotificationSettings.as_view(),
        name='notification_settings',
    ),

    # added by tplick on 28 February 2018
    url(
        regex=r'^get_previously_viewed_profiles$',
        view=views.PreviouslyViewedProfilesView.as_view(),
        name='get_previously_viewed_profiles',
    ),

    # added by tplick on 4 April 2018
    url(
        regex=r'^delete_job/(?P<employer_job_id>\d+)$',
        view=views.DeleteJobView.as_view(),
        name='delete_job',
    ),

    url(
        regex=r'^company_description$',
        view=views.CompanyDescriptionPostView.as_view(),
        name='company_description',
    ),

    # added by tplick on 8 June 2018
    url(
        regex=r'^get_headshot_url/(?P<employer_user_id>\d+)$',
        view=views.GetHeadshotUrlView.as_view(),
        name='get_headshot_url',
    ),
    url(
        regex=r'^upload_headshot/(?P<employer_user_id>\d+)$',
        view=views.HeadshotUploadView.as_view(),
        name='upload_headshot',
    ),
    url(
        regex=r'^remove_headshot/(?P<employer_user_id>\d+)$',
        view=views.HeadshotRemovalView.as_view(),
        name='remove_headshot',
    ),

    url(
        regex=r'^stats$',
        view=views.EmployerStatsView.as_view(),
        name='stats',
    ),

    # added by nsymer on 30 Sept 2018
    url(
        regex=r'^contact_info/(?P<candidate_id>\d+)$',
        view=views.CandidateContactView.as_view(),
        name='contact_info'
    ),

    # added by natesymer on 11.14.18
    url(
        regex=r'^preview_intro/(?P<employer_job_id>\d+)$',
        view=views.EmployerPreviewCandidateContact.as_view(),
        name='preview_intro'
    )
]
