__author__ = "natesymer"

import json
from functools import partial

from django.utils import timezone
from django.db import connection

from .util import HourlyTask, DailyTask, WeekdayDailyTask, WeeklyTask, Days
from . import util

from bakround_applicant.stats import weekly_emails
from bakround_applicant.services.queue import QueueNames, QueueConnection
from bakround_applicant.services.notificationservice.util import send_follow_up_emails
from bakround_applicant.verifier.email_watcher import watch_for_indeed_emails

def set_task_array(array):
    util.ALL_TASKS = array

def create_tasks():
    HourlyTask("refresh search_profile_view",
               partial(QueueConnection.quick_publish, queue_name=QueueNames.on_demand_view_refresher)).register()

    HourlyTask("watch for incoming indeed emails",
               watch_for_indeed_emails).register()
    DailyTask("send follow-up emails to candidates",
              send_follow_up_emails,
              hour=21).register()

