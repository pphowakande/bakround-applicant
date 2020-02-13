__author__ = "natesymer"

import bakround_applicant.scheduler.tasks
import bakround_applicant.scheduler.util

class Consumer:
    def __init__(self):
        pass

    def consume(self):
        bakround_applicant.scheduler.tasks.create_tasks()
        bakround_applicant.scheduler.util.scheduler_loop()

