
__author__ = "tplick"

import json
from bakround_applicant.services.queue import QueueConnection, QueueNames


from bakround_applicant.utilities.logger import LoggerFactory
logger = LoggerFactory.create('EVENT_SERVICE')


class EventActions:
    resume_upload = 'resume_upload'
    profile_edit = 'profile_edit'
    profile_printview_generate = 'profile_printview_generate'
    profile_external_viewer_add = 'profile_external_viewer_add'
    profile_external_viewer_remove = 'profile_external_viewer_remove'
    score_regeneration_request = 'score_regeneration_request'
    score_analysis_view = 'score_analysis_view'
    employer_job_create = 'employer_job_create'
    employer_job_update = 'employer_job_update'
    employer_job_export = 'employer_job_export'
    employer_job_candidate_add = 'employer_job_candidate_add'
    employer_job_candidate_contact = 'employer_job_candidate_contact'
    employer_job_candidate_remove = 'employer_job_candidate_remove'
    employer_job_closed = 'employer_job_closed'
    employer_job_reopened = 'employer_job_reopened'
    employer_job_search = 'employer_job_search'
    employer_profile_view = 'employer_profile_view'
    employer_user_create = 'employer_user_create'
    employer_user_delete = 'employer_user_delete'
    employer_user_update = 'employer_user_update'
    employer_custom_email_body_save = 'employer_custom_email_body_save'
    employer_logo_upload = 'employer_logo_upload'
    employer_candidate_status_open = 'employer_candidate_status_open'
    employer_candidate_status_update = 'employer_candidate_status_update'
    employer_resume_upload = 'employer_resume_upload'
    employer_custom_job_create = 'employer_custom_job_create'
    employer_custom_job_update = 'employer_custom_job_update'
    employer_custom_job_delete = 'employer_custom_job_delete'


def record_event(user, action, metadata=None):
    from .models import Event

    if not user.is_anonymous:
        Event(user=user,
              action=action,
              metadata=metadata).save()
