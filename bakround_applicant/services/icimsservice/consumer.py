__author__ = 'poonam'

import json

from bakround_applicant.services.base import BaseConsumer, FatalException, NonfatalException
from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.browsing.util import icims_spider
from bakround_applicant.all_models.db import ProfileResume,Job, RankingJob, IcimsJobData, Profile, ProfileJobMapping, IcimsProfileJobMapping

class Consumer(BaseConsumer):
    service_name = 'RANKING_SVC'
    queue_name = QueueNames.icims_service

    def handle_message(self, body):
        message = json.loads(body)
        ranking_job_id = message.get("ranking_job_id")
        if not ranking_job_id:
            self.logger.error("{}: missing ranking_job_id parameter.".format(self.service_name))
            raise FatalException()

        ranking_job = RankingJob.objects.filter(pk=ranking_job_id).first()
        if not ranking_job:
            self.logger.error("{}: ranking job does not exist: {}".format(self.service_name, ranking_job_id))
            raise FatalException()

        ranking_job.running = True
        ranking_job.save()

        self.source = ranking_job.source

        self.logger.info("Ranking {} RankingJob {}".format(ranking_job.source, ranking_job.id))

        def on_resume(data, url):
            job_name = data["icims_job"][0]["value"]

            job_data = list(Job.objects.filter(job_name=job_name))
            if len(job_data)>0:
                job_id = job_data[0].id
            else:
                job_data = list(Job.objects.filter(job_name__icontains=job_name).order_by('job_name'))
                if len(job_data)>0:
                    job_id = job_data[0].id
                else:
                    job_id = 1

            ranking_job_id = IcimsJobData.objects.get(job_title = job_name)
            previously_scraped = ProfileResume.objects.filter(url=url).order_by('-date_created').first()

            # Always create a new ProfileResume to preserve precious data
            profile_resume = ProfileResume(
                url=url,
                source=ranking_job.source,
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
            ranking_job.job_id = job_id

            # Ensure that the attached profile is mapped to at least one icims job.
            if not IcimsProfileJobMapping.objects.filter(profile_id=profile_resume.profile_id,
                                                        job_id=ranking_job.job_id,
                                                        icims_job_id=ranking_job_id).exists():
                IcimsProfileJobMapping(profile_id=profile_resume.profile_id,
                                  job_id=ranking_job.job_id,
                                  icims_job_id=ranking_job_id).save()
                self.logger.info("Mapped Icims Profile id {} to icims Job id {}.".format(profile_resume.profile_id,
                                                                             ranking_job_id))

            self.logger.info("Created ProfileResume id {}{}.".format(profile_resume.id, " (previously scraped)" if previously_scraped else ""))

            ranking_job.refresh_from_db()


            # Ensure that the attached profile is mapped to at least one job.
            if not ProfileJobMapping.objects.filter(profile_id=profile_resume.profile_id,
                                                        job_id=ranking_job.job_id).exists():
                ProfileJobMapping(profile_id=profile_resume.profile_id,
                                  job_id=ranking_job.job_id).save()
                self.logger.info("Mapped Profile id {} to Job id {}.".format(profile_resume.profile_id,
                                                                             ranking_job.job_id))

            self.logger.info("Created ProfileResume id {}{}.".format(profile_resume.id, " (previously scraped)" if previously_scraped else ""))

            ranking_job.refresh_from_db()
            if previously_scraped: ranking_job.resumes_rescraped += 1
            else:                  ranking_job.new_resumes_scraped += 1
            ranking_job.save()

            QueueConnection.quick_publish(
                queue_name=QueueNames.build_profile,
                body=json.dumps({
                    'profile_id': profile_resume.profile.id,
                    'profile_resume_id': profile_resume.id,
                    'source':ranking_job.source
            }))
            return True

        if ranking_job.source == "icims":
            icims_spider(ranking_job, on_resume)
        else:
            raise FatalException()
