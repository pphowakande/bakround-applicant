__author__ = 'natesymer'

import os
import json
import sys

from .queue import QueueConnection
from bakround_applicant.utilities.logger import LoggerFactory
from bakround_applicant.utilities.functions import is_production
from bakround_applicant.utilities.sentry import forward_exception_to_sentry

class FatalException(Exception):
    pass

class NonfatalException(Exception):
    pass

class TimeoutException(Exception):
    pass

class BaseConsumer:
    # props to override
    service_name = "BASE_SVC"
    concurrency = 1
    queue_name = None

    # props to use
    queue_connection = None
    logger = None

    def __init__(self):
        self.logger = LoggerFactory.create(self.service_name)
        self.queue_connection = QueueConnection()

    def send_message(self, queue_name, body, **kwargs):
        self.queue_connection.publish(queue_name=queue_name,
                                      body=body,
                                      **kwargs)

    # stub for inheriting classes to override
    def handle_message(self, body):
        return

    # stub for inheriting classes to override
    def pre_consume(self):
        return

    def consume(self):
        def callback(body, reject, resolve):
            self.logger.info("Received {}".format(body))

            try:
                self.handle_message(body.decode('UTF-8'))
                resolve()
            except Exception as e:
                ename = sys.exc_info()[0].__name__
                if ename == "FatalException":
                    self.logger.error("FatalException received.")
                    reject(requeue = False)
                    sys.exit(1)
                else:
                    if ename == "TimeoutException":
                        self.logger.info("Timed out.")
                    elif ename == "NonfatalException":
                        self.logger.info("Non-fatal exception.")
                    else:
                        forward_exception_to_sentry()
                        self.logger.error("Unexpected error.")
                    reject(requeue = True)

        self.pre_consume()
        self.queue_connection.consume(queue_name=self.queue_name, callback=callback, max_number_threads=self.concurrency)

    class Meta:
        abstract = True
