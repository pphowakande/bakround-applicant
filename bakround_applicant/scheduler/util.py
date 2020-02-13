
__author__ = "tplick"

from ..all_models.db import User
from ..scheduler.models import SchedulerLastRun
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import time

ALL_TASKS = []


from ..utilities.logger import LoggerFactory
logger = LoggerFactory.create("SCHEDULER")


class Days:
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Task:
    def run(self):
        self.fn()

    def register(self):
        ALL_TASKS.append(self)

    def now(self):
        return timezone.now()


class DailyTask(Task):
    def __init__(self, name, fn, hour):
        self.name = name
        self.fn = fn
        self.hour = hour

    def should_run_now(self):
        now = self.now()
        return now.hour == self.hour


class WeekdayDailyTask(Task):
    def __init__(self, name, fn, hour):
        self.name = name
        self.fn = fn
        self.hour = hour

    def should_run_now(self):
        now = self.now()
        return now.hour == self.hour and now.weekday() < 5


class HourlyTask(Task):
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def should_run_now(self):
        return True


class WeeklyTask(Task):
    def __init__(self, name, fn, hour, day_of_week):
        self.name = name
        self.fn = fn
        self.hour = hour
        self.day_of_week = day_of_week

    def should_run_now(self):
        now = self.now()
        return now.hour == self.hour and now.weekday() == self.day_of_week


def try_to_run_scheduler():
    with connection.cursor() as cursor:
        cursor.execute("select pg_advisory_lock(101)")

        try:
            now = timezone.now()
            if now.minute >= 15:
                return False

            if not has_scheduler_run_recently():
                update_last_run_date()
                run_tasks()
                return True
            else:
                return False

        finally:
            cursor.execute("select pg_advisory_unlock(101)")


def has_scheduler_run_recently():
    last_run_record = SchedulerLastRun.objects.first()
    if last_run_record:
        return last_run_record.last_run_date >= timezone.now() - timedelta(minutes=30)
    else:
        return False


def update_last_run_date():
    last_run_record, was_created = SchedulerLastRun.objects.get_or_create()
    last_run_record.last_run_date = timezone.now()
    last_run_record.save()


def run_tasks():
    tasks_to_run = []

    for task in ALL_TASKS:
        if task.should_run_now():
            tasks_to_run.append(task)

    for task in tasks_to_run:
        try:
            task.run()
            logger.info('task {} ran successfully'.format(task.name))
        except Exception as e:
            logger.error('error while running task {}:'.format(task.name))
            logger.exception(e)


def scheduler_loop():
    while True:
        now = timezone.now()
        if now.minute < 15:
            try_to_run_scheduler()
            time.sleep(1800)
        else:
            time.sleep(60)
