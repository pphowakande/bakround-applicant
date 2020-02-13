#!/usr/bin/env python3
import sys
import re
import calendar
from bakround_applicant.all_models.db import ICIMSLastUpdatedDate, ICIMSApplicantWorkflowData
from bakround_applicant.all_models.db import LookupState, LookupDegreeMajor, IcimsJobData
from django.db.models import Q
from datetime import datetime, timedelta
import base64


class SanitationRanking():

    def __init__(self):
        self.ICIMS_SANDBOX_USERNAME = "Bakroundapiuser1"
        self.ICIMS_SANDBOX_PASSWORD = "Poon@m90"
        self.ICIMS_PRODUCT = "candidate_ranking"

    def generate_request_headers(self):
        AUTH_KEY_BASE64 = self.generate_auth_key(self.ICIMS_SANDBOX_USERNAME, self.ICIMS_SANDBOX_PASSWORD)
        headers = {
            'Authorization': "Basic {}".format(AUTH_KEY_BASE64),
            'Content-Type': "application/json",
        }
        return headers

    def generate_auth_key(self,ICIMS_SANDBOX_USERNAME, ICIMS_SANDBOX_PASSWORD):
        # create base64 auth key for icims authentication
        AUTH_KEY = self.ICIMS_SANDBOX_USERNAME + ":" + self.ICIMS_SANDBOX_PASSWORD
        AUTH_KEY_BASE64 = base64.b64encode(AUTH_KEY.encode())
        return AUTH_KEY_BASE64.decode()

    def extract_last_updated_date(self):
        last_updated_date = ICIMSLastUpdatedDate.objects.filter(Q(product_name=self.ICIMS_PRODUCT)).last()
        if last_updated_date is not None:
            return last_updated_date.last_updated_date
        return None

    def save_icims_job(self,job_link, job_title):
        # check if job link already present
        job_data = IcimsJobData.objects.filter(Q(job_link=job_link)).first()
        if job_data is not None:
            pass
        else:
            #save in database
            icims_job = IcimsJobData()
            icims_job.job_link = job_link
            icims_job.job_title = job_title
            icims_job.save()
            return True

    def save_applicant_workflow(self,workflow_id,workflow_url,person_id,person_name,person_url,job_url):
        applicant_workflow = ICIMSApplicantWorkflowData()
        applicant_workflow.product_name = self.ICIMS_PRODUCT
        applicant_workflow.workflow_id = workflow_id
        applicant_workflow.workflow_url = workflow_url
        applicant_workflow.person_id = person_id
        applicant_workflow.person_name = person_name
        applicant_workflow.person_url = person_url
        applicant_workflow.job_url = job_url
        applicant_workflow.save()
        return True

    def update_score_flag(self, workflow_url, assessment_update_url):
        changes = {}
        changes = {"is_scored":True,"assessment_update_url": assessment_update_url}
        icims_applcnt_workflow_data = ICIMSApplicantWorkflowData.objects.filter(workflow_url=workflow_url)
        icims_applcnt_workflow_data.filter(workflow_url=workflow_url).update(**changes)
        return True

    def add_last_updated_date(self):
        print("inside add_last_updated_date function----------")
        icims_last_updated_date = ICIMSLastUpdatedDate()
        icims_last_updated_date.product_name = self.ICIMS_PRODUCT
        print("datetime.today() : ", datetime.today())
        # last_updated_date = datetime.today() + timedelta(hours=5) + timedelta(minutes=30)
        last_updated_date = datetime.today() + timedelta(minutes=1)
        last_updated_date =  last_updated_date.strftime('%Y-%m-%d %I:%M %p')
        icims_last_updated_date.last_updated_date = str(last_updated_date)
        icims_last_updated_date.save()
        return True

    def extract_state(self, state):
        state = LookupState.objects.filter(Q(state_code=state) | Q(state_name=state)).first()
        return state

    def get_assessment_update_url(self, workflow_id):
        assessment_update_url = ICIMSApplicantWorkflowData.objects.filter(Q(workflow_id=workflow_id)).values_list("assessment_update_url").first()
        return assessment_update_url[0]
