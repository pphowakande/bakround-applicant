__author__ = 'natesymer'

import json

from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from bakround_applicant.all_models.db import Notification, EmployerUser, EmployerCandidate
from bakround_applicant.verifier.utilities import request_verification_for
from . import util
from ..queue import QueueNames
from ..base import BaseConsumer
from .exceptions import UnspecifiedRecipientException, EmailNotFoundException, UnverifiedNameException

class Consumer(BaseConsumer):
    service_name = "NOTIFICATION_SVC"
    concurrency = 3
    queue_name = QueueNames.notification_service

    def handle_message(self, body):
        msg = json.loads(body)

        if not msg.get('notification_id'):
            raise ValueError('notification_id was not specified in queue message')

        notification_id = int(msg['notification_id'])
        notification = Notification.objects.get(id=notification_id)

        resend = msg.get('resend') or False

        try:
            if notification.sent and notification.follow_up_count == 0:
                self.logger.info('Notification id {} has already been sent'.format(notification.id))
            elif notification.type == 'email':
                to_email = util.send_email_notification(notification=notification, resend = resend)
                self.logger.info('Sent emails to {} for Notification id {}.'.format(to_email, notification.id))
        except (EmailNotFoundException, UnverifiedNameException) as e:
            email_not_found = type(e) is EmailNotFoundException
            self.logger.info("Missing {} for Profile id {}.".format("email address" if email_not_found else "verified name", e.profile_id))
            request_verification_for(e.profile_id,
                                     callback_queue=Consumer.queue_name,
                                     callback_message=msg,
                                     metadata=notification.metadata)
        except UnspecifiedRecipientException:
            self.logger.info('Unspecified recipient for for Notification id {}.'.format(notification.id))
        except:
            # TODO: re-examine this.
            notification.refresh_from_db()
            if notification.sender_profile and notification.sender_profile.id:
                request_verification_for(notification.sender_profile.id,
                                         callback_queue=Consumer.queue_name,
                                         callback_message=msg,
                                         metadata=notification.metadata)

            if notification.recipient_profile and notification.recipient_profile.id:
                request_verification_for(notification.recipient_profile.id,
                                         callback_queue=Consumer.queue_name,
                                         callback_message=msg,
                                         metadata=notification.metadata)
            raise

