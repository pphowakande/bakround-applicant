__author__ = "poonam"

from bakround_applicant.ranking.icims.sanitation import SanitationRanking
from ... import BrowserAction
from datetime import datetime, timedelta
import json
import requests

class CrawlIcims(BrowserAction):

    # BrowserAction
    ranking_job = None

    def get_start_offset(self):
        self.ranking_job.refresh_from_db()
        return self.ranking_job.start_offset

    def finish_crawling(self):
        self.ranking_job.refresh_from_db()
        self.ranking_job.running = False
        self.ranking_job.save()

    def go(self, browser):
        counter = 0
        while True:
            print("Starting process-------Getting candidates urls")

            start_offset = self.get_start_offset()
            # create sanitation object
            sanitation_obj = SanitationRanking()
            # generate request headers
            headers = sanitation_obj.generate_request_headers()

            # query database to find out last run date- search table "ICIMSLastUpdatedDate"
            last_updated_date = sanitation_obj.extract_last_updated_date()
            print("last_updated_date DB : ", last_updated_date)
            if last_updated_date is None:
                days_to_subtract  = 90
                last_updated_date = datetime.today() - timedelta(days=days_to_subtract) + timedelta(hours=5) + timedelta(minutes=30)
                last_updated_date = last_updated_date.strftime('%Y-%m-%d %I:%M %p')

            print("last_updated_date final : ", last_updated_date)
            # Once we have number of days, lets search for applicant workflows
            payload = "{\"filters\": [{\"name\": \"applicantworkflow.updateddate\",\"value\": [\"" + str(last_updated_date) + "\"],\"operator\": \">=\"}],\"operator\": \"&\"}"
            print("payload : ", payload)
            workflow_endpoint ="https://api.icims.com/customers/8611/search/applicantworkflows"
            response = requests.request("POST", workflow_endpoint, data=payload, headers=headers)
            print("response.status_code : ", response.status_code)
            if response.status_code == 200:
                response = response.json()
                results = response["searchResults"]
                if len(results)==0:
                    self.logger.info("No candidates found.")
                    self.finish_crawling()
                    break

                print("start_offset : ", start_offset)
                print("counter : ", counter)

                if start_offset > 0:
                    counter = counter + start_offset

                if len(results) == counter:
                    print("------------------SCRAPING FINISH--------------------")
                    break
                print("*************TOTAL URLS :************" , len(results))
                for each_workflow in range(len(results)):
                    if start_offset > 0:
                        start_offset = start_offset - 1
                    else:
                        counter = counter + 1
                        applicant_workflow_endpoint = results[each_workflow]["self"]
                        self.logger.info("Found Icims candidate url: {}".format(applicant_workflow_endpoint))
                        yield str(applicant_workflow_endpoint)
                        self.ranking_job.refresh_from_db()
                        self.ranking_job.start_offset += 1
                        self.ranking_job.save()

                print("************DONE WITH ALL URLS*******************")
                # save last updated here
                sanitation_obj.add_last_updated_date()
            else:
                self.logger.info("Error response from ICIMS---- ", response.status_code)
                self.finish_crawling()
                break
