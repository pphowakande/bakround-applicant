__author__ = 'tplick'

import json
from ..queue import QueueNames
from ..base import BaseConsumer
from bakround_applicant.all_models.db import UserEvent


class Consumer(BaseConsumer):

    service_name = "EVENT_SVC"
    queue_name = QueueNames.event_service

    def handle_message(self, body):
        message = json.loads(body)
        user_id = message['user_id']
        action = message['action']
        metadata = message['metadata']

        UserEvent(user_id=user_id,
                  action=action,
                  metadata=metadata).save()
