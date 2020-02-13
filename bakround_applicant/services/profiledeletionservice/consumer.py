
__author__ = "tplick"

import json
from ..queue import QueueNames
from ..base import BaseConsumer
from bakround_applicant.all_models.db import Profile

class Consumer(BaseConsumer):
    service_name = "PROFILE_DELETION_SVC"
    queue_name = QueueNames.profile_deletion

    def handle_message(self, body):
        msg = json.loads(body)
        profile_id = msg['profile_id']

        try:
            profile = Profile.objects.get(id=profile_id)
            if not profile.queued_for_deletion:
                raise Exception("profile {} does not have queued_for_deletion set".format(profile.id))

            self.logger.info('deleting profile {}'.format(profile_id))
            profile.delete()

        except Exception as e:
            logger.exception(e)

