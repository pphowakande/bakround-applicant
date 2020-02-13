__author__ = 'natesymer'

import os
import json
from datetime import datetime, timedelta

from ..queue import QueueNames
from ..base import BaseConsumer
from bakround_applicant.all_models.db import ScoreRequest, Profile, Job, ProfileJobMapping
from bakround_applicant.score.util import get_score, queue_request, ScoreGenerationException, InvalidScoreRequestException
from bakround_applicant.ranking.icims.get_score import return_bscore

class Consumer(BaseConsumer):
    service_name = 'SCORING_SVC'
    concurrency = 4
    queue_name = QueueNames.scoring_service

    # Consists of several modes:
    # single: score a profile.
    # Other modes are implemented using `single`. TODO: document them.

    def single(self, message):
        """Primary code path for scoring. Actually scores a profile!"""
        # Load parameters from `message`
        skip_delta_days = int(message.get('skip_delta_days') or 0) or None
        score_request_id = message.get("score_request_id") # NEW

        profile_id = message.get("profile_id") or None
        source = message.get("source") or None
        profile_resume_id = message.get("profile_resume_id") or None
        if not score_request_id:
            raise ValueError("Missing `score_request_id`.")

        # Attempt to coerce `score_request_id` into an `int`.
        try:
            score_request_id = int(score_request_id)
        except:
            raise ValueError("`score_request_id` should be an integer. Supplied value: `{}`".format(score_request_id))

        # Grab the relevant score request
        score_request = ScoreRequest.objects.filter(id=score_request_id).first() # NEW

        if not score_request:
            self.logger.info("ScoreRequest id {} does not exist.".format(score_request_id))
            return

        # If the score was created up to `skip_delta_days` ago, don't rescore.
        if skip_delta_days:
            max_age = datetime.now() - timedelta(days=skip_delta_days)
            if Score.objects.filter(profile_id=score_request.profile_id,
                                    date_created__gte=max_age).exists():
                self.logger.info("Skipping ScoreRequest id {}.".format(score_request.id))
                return

        # Get a score
        try:
            score = get_score(score_request) # NEW
        except ScoreGenerationException as e: # NEW
            self.logger.error("{} (Profile id {}, Job id {})".format(str(e), e.profile_id, e.job_id))
            return
        except InvalidScoreRequestException as e: # NEW
            self.logger.error("Invalid score request: {} (Profile id {}, Job id {})".format(str(e), e.profile_id, e.job_id))
            return

        # Save the score & update the scoring request.
        score.save()
        score_request.completed = True
        score_request.score_id = score.id
        score_request.save()

        self.logger.info("Created Score id {} ({}) (Profile id {}, Job id {})".format(score.id,
                                                                                      score.score_value,
                                                                                      score.profile_id,
                                                                                      score.job_id))

        # if source=icims , send back bscore  and update is_scored = true in database
        if source == "icims":
            return_bscore(score.score_value, profile_resume_id)



    def system(self, message):
        job_id = int(message.get('job_id'))
        if not job_id:
            raise ValueError('Missing or invalid job_id: {}'.format(job_id))

        for profile_id in ProfileJobMapping.objects.filter(job_id=job_id).values_list("profile_id", flat=True).iterator():
            score_request = ScoreRequest(profile_id=profile_id, job_id=job_id)
            score_request.save()

            queue_request(score_request, skip_delta_days=message.get('skip_delta_days'))

        self.send_message(queue_name=QueueNames.scoring_service,
                          body=json.dumps({'mode': 'mark_scoring_as_done',
                                           'job_id': job_id}))

    def custom_jobs(self, message):
        job_ids = list(Job.objects.filter(is_waiting_to_be_scored=True)
                                          .values_list('id', flat=True))
        for job_id in job_ids:
            self.logger.info('triggering batch rescore for job {}'.format(job_id))
            self.send_message(queue_name=QueueNames.scoring_service,
                              body=json.dumps({'mode': 'system',
                                               'job_id': job_id}))

    def job_family(self, message):
        job_family_id = int(message['job_family_id'])
        self.logger.info('rescoring profiles for job family {}'.format(job_family_id))

        mappings = ProfileJobMapping.objects.filter(job__job_family_id=job_family_id, job__accuracy__gte=2)
        for m in mappings:
            score_request = ScoreRequest(profile_id=m.profile_id, job_id=m.job_id)
            score_request.save()
            queue_request(score_request)

    def mark_done(self, message):
        job_id = int(message['job_id'])
        job = Job.objects.get(id=job_id)
        job.is_waiting_to_be_scored = False
        job.has_ever_been_scored = True
        job.save()

    def pending(self, message):
        map(queue_request, ScoreRequest.objects.filter(completed=False))

    def handle_message(self, body):
        message = json.loads(body)
        mode = message.get('mode')
        if not mode:
            raise Exception('Invalid message, missing mode')

        if mode == 'single':
            self.single(message)
        elif mode == 'system':
            self.system(message)
        elif mode == 'pending':
            self.pending(message)
        elif mode == 'custom_jobs':
            self.custom_jobs(message)
        elif mode == 'job_family':
            self.job_family(message)
        elif mode == 'mark_scoring_as_done':
            self.mark_done(message)
        else:
            raise Exception('Invalid mode value')
