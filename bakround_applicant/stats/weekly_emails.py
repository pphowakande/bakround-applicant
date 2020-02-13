__author__ = 'tplick'

import sys
import json
import time
import html

from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.services.statsservice.models import Stats
from bakround_applicant.stats.logic import get_stats
from bakround_applicant.stats.new_users import get_new_user_stats
from bakround_applicant.stats.employer import get_employer_stats_html
from bakround_applicant.all_models.db import Notification, EmployerUser, Employer, \
                                             EmployerJob, EmployerCandidate

from bakround_applicant.utilities.logger import LoggerFactory

class WeeklyStats:
    def __init__(self):
        self.logger = LoggerFactory.create("WEEKLY_STATS")

    def queue_notification(self, _id):
        QueueConnection.quick_publish(QueueNames.notification_service, json.dumps({ "notification_id": _id }))

    def generate_stats(self, mode, employer_id=None):
        todays_date = time.strftime("%B %d, %Y")

        if mode == Stats.profile_stats:
            stats_text = get_stats()
            stats_html = "<pre>" + html.escape(stats_text) + "</pre>"

            notification = Notification(type='email',
                                        sender_email='no-reply@bakround.com',
                                        recipient_email='stats@bakround.com',
                                        subject="Profile stats as of {}".format(todays_date),
                                        body=stats_text,
                                        html_body=stats_html)
            notification.save()

            self.queue_notification(notification.id)
            self.logger.info('queued internal weekly stats notification for mode={}'.format(mode))
        elif mode == Stats.new_user_stats:
            stats_text = get_new_user_stats()
            stats_html = "<pre>" + html.escape(stats_text) + "</pre>"

            notification = Notification(type='email',
                                        sender_email='no-reply@bakround.com',
                                        recipient_email='stats@bakround.com',
                                        subject="New user stats for {}".format(todays_date),
                                        body=stats_text,
                                        html_body=stats_html)
            notification.save()

            self.queue_notification(notification.id)
            self.logger.info('queued internal weekly stats notification for mode={}'.format(mode))
        elif mode == Stats.employer_stats:
            if employer_id is None:
                raise Exception('employer_id was not specified in the queue message')

            stats_html = get_employer_stats_html(employer_id)

            for employer_user in EmployerUser.objects.filter(employer_id=employer_id,
                                                             weekly_stats_email_enabled=True):

                notification = Notification(type='email',
                                            sender_email='no-reply@bakround.com',
                                            recipient_email=employer_user.user.email,
                                            subject='Bakround - Weekly Job Stats',
                                            body=stats_html,
                                            html_body=stats_html)
                notification.save()

                self.queue_notification(notification.id)
                self.logger.info('queued weekly stats notification for mode={}, employer_id={}, user={} {}'.format(mode,
                                                                                                                   employer_id,
                                                                                                                   employer_user.user.first_name,
                                                                                                                   employer_user.user.last_name))
            employer = Employer.objects.get(pk=employer_id)
            notification = Notification(type='email',
                                        sender_email='no-reply@bakround.com',
                                        recipient_email='stats@bakround.com',
                                        subject='{} - Weekly Job Stats'.format(employer.company_name),
                                        body=stats_html,
                                        html_body=stats_html)
            notification.save()

            queue_notification(notification.id)
            self.logger.info('queued internal weekly stats notification for mode={}, employer_id={}'.format(mode,
                                                                                                            employer_id))

        return


def trigger_emails():
    obj = WeeklyStats()
    obj.generate_stats(Stats.profile_stats)
    obj.generate_stats(Stats.new_user_stats)

    # AN - excluding Hospitality employers per Eric
    for employer in Employer.objects.exclude(job_family_id=2).order_by('id'):
        if EmployerJob.objects.filter(employer=employer).exists():
            obj.generate_stats(Stats.employer_stats, employer.id)
