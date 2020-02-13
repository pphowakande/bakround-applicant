__author__ = "natesymer"

import json

from django.db import connection, transaction
from django.utils import timezone

from ..queue import QueueNames
from bakround_applicant.services.base import BaseConsumer
from bakround_applicant.all_models.db import Job, ProfileJobMapping
from bakround_applicant.score.util import queue_job_rescore

class Consumer(BaseConsumer):
    service_name = "MAPPING_SERVICE"
    queue_name = QueueNames.mapping_service

    def ids_query(self, sql):
        with connection.cursor() as cursor:
            cursor.execute(sql)
            for (ID,) in cursor:
                yield ID

    def handle_message(self, body):
        message = json.loads(body)
        job_id = int(message.get('job_id'))

        if not job_id:
            raise ValueError("Falsey job_id: {}".format(message.get('job_id')))

        job = Job.objects.get(id=job_id)

        self.logger.info("Remapping Job id {}.".format(job.id))
        
        def id_to_mapping(_id):
            return ProfileJobMapping(profile_id=_id, job_id=job.id)
        
        with transaction.atomic():
            ids = self.ids_query(job.remap_query)
            ProfileJobMapping.objects.filter(job_id=job.id).delete()
            ProfileJobMapping.objects.bulk_create(list(map(id_to_mapping, ids)))
        
            job.last_remap_date = timezone.now()
            job.save(update_fields=['last_remap_date'])
        
        self.logger.info("Finished remapping Job id {}, queing profiles for scoring.".format(job.id))
        
        queue_job_rescore(job.id, skip_delta_days=5)

