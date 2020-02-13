__author__ = 'natesymer'

import json

from bakround_applicant.services.base import BaseConsumer, FatalException, NonfatalException
from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.browsing import BrowserFatalError, BrowserRecoverableError, BrowserActionFatalError, BrowserActionNonFatalError
from bakround_applicant.browsing.util import indeed_spider
from bakround_applicant.all_models.db import ProfileResume, ScraperJob, Profile, ProfileJobMapping

class Consumer(BaseConsumer):
    service_name = 'SCRAPING_SVC'
    concurrency = 10
    queue_name = QueueNames.scraping_service

    def handle_message(self, body):
        message = json.loads(body)
        scraper_job_id = message.get("scraper_job_id")
        if not scraper_job_id:
            self.logger.error("{}: missing scraper_job_id parameter.".format(self.service_name))
            raise FatalException()

        scraper_job = ScraperJob.objects.filter(pk=scraper_job_id).first()
        if not scraper_job:
            self.logger.error("{}: scraper job does not exist: {}".format(self.service_name, scraper_job_id))
            raise FatalException()

        scraper_job.running = True
        scraper_job.save()

        self.logger.info("Scraping {} ScraperJob {}".format(scraper_job.source, scraper_job.id))

        def on_resume(data, url):
            previously_scraped = ProfileResume.objects.filter(url=url).order_by('-date_created').first()

            # Always create a new ProfileResume to preserve precious data
            profile_resume = ProfileResume(
                url=url,
                source=scraper_job.source,
                parser_output=data
            )

            # Copy over the profile from the old resume, if it exists
            if previously_scraped and previously_scraped.profile:
                profile_resume.profile = previously_scraped.profile

            # Ensure the ProfileResume has an attached profile.
            if not profile_resume.profile:
                p = Profile()
                p.save()
                profile_resume.profile = p

            profile_resume.save()

            # Ensure that the attached profile is mapped to at least one job.
            if not ProfileJobMapping.objects.filter(profile_id=profile_resume.profile_id,
                                                        job_id=scraper_job.job_id).exists():
                ProfileJobMapping(profile_id=profile_resume.profile_id,
                                  job_id=scraper_job.job_id).save()
                self.logger.info("Mapped Profile id {} to Job id {}.".format(profile_resume.profile_id,
                                                                             scraper_job.job_id))

            self.logger.info("Created ProfileResume id {}{}.".format(profile_resume.id, " (previously scraped)" if previously_scraped else ""))

            scraper_job.refresh_from_db()
            if previously_scraped: scraper_job.resumes_rescraped += 1
            else:                  scraper_job.new_resumes_scraped += 1
            scraper_job.save()

            print("scraper_job saved--------------")

            print("Starting build profile service now----------")
            print("profile_resume.profile.id : ", profile_resume.profile.id)
            print("profile_resume.id : ", profile_resume.id)

            QueueConnection.quick_publish(
                queue_name=QueueNames.build_profile,
                body=json.dumps({
                    'profile_id': profile_resume.profile.id,
                    'profile_resume_id': profile_resume.id
            }))
            return True

        try:
            if scraper_job.source == "indeed":
                indeed_spider(scraper_job, on_resume)
            else:
                raise FatalException()
        except (BrowserFatalError, BrowserRecoverableError, BrowserActionFatalError, BrowserActionNonFatalError):
            # Restart the service, requeue message
            raise NonfatalException()
