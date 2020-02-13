__author__ = 'natesymer'

import os
import threading
import queue
from functools import partial
from contextlib import contextmanager

import pika
import time
from django.db import transaction

from bakround_applicant.utilities.logger import LoggerFactory

def swallow(callback):
    """Swallows all exceptions"""
    try: callback()
    except: pass

class QueueNames:
    mapping_service = "mapping-service-q" #present
    scoring_service = "scoring-service-q" #present
    build_profile = "build-profile-q"#present
    scraping_service = "scraping-service-q" #present
    verifying_service = 'verifying-service-q' #present
    notification_service = 'notification-service-q' #present
    on_demand_view_refresher = 'on-demand-view-refresher-q' #present
    profile_deletion = 'profile-deletion-q' #present
    profile_data = 'profile-data-q'
    people_search = 'people-search-q'
    event_service = 'event-service-q' #present
    stats_service = 'stats-service-q'
    icims_service = 'icims-service-q'

# queues not appearing in this dictionary are not priority queues
MAX_PRIORITIES = {QueueNames.scoring_service: 1}

class QueueConnection:
    # Logic parameters
    max_number_threads = 1
    max_retries = 3

    # Configurable RabbitMQ connection parameters
    heartbeat_interval = 10
    connection_attempts = 3
    backpressure_detection = True

    def __init__(self):
        self.logger = LoggerFactory.create("QueueConnection_{}".format(id(self)))
        self.threads = []
        self.thread_queue = queue.Queue()
        self.active_connections = []

    @property
    def host(self):
        return os.getenv('RABBITMQ_HOST') or None

    @property
    def port(self):
        v = os.getenv('RABBITMQ_PORT') or None
        if v:
            try: v = int(v)
            except: v = None
        return v or None

    @property
    def virtual_host(self):
        return os.getenv('RABBITMQ_VIRTUAL_HOST') or '/'

    @property
    def username(self):
        return os.getenv('RABBITMQ_USER') or None

    @property
    def password(self):
        return os.getenv('RABBITMQ_PASSWORD') or None

    @classmethod
    def quick_publish(cls, queue_name, body='{}', headers=None, priority=None):
        """Just a shortcut. If we're in a Django transaction, schedule the publish
           to occur when the transaction commits."""

        try:
            in_block = transaction.get_connection().in_atomic_block
        except:
            in_block = False

        def go():
            q.publish(queue_name, body, headers=headers, priority=priority)

        q = cls()
        if in_block:
            transaction.on_commit(go)
        else:
            go()

    def publish(self, queue_name, body='{}', headers=None, priority=None):
        if not queue_name:
            raise ValueError("Missing queue_name.")

        if not body:
            raise ValueError("Missing body.")

        with self.rabbitmq() as (connection, channel):
            self._basic_declare(channel, queue_name)
            self._basic_publish(channel, queue_name, body, headers, priority)

    def purge(self, queue_name):
        if not queue_name:
            raise ValueError("Missing queue_name.")

        with self.rabbitmq() as (connection, channel):
            self._basic_declare(channel, queue_name)
            self._basic_purge(channel, queue_name)

    def consume(self, queue_name, callback, max_number_threads=None):
        """Multithreaded RabbitMQ queue consumer."""
        with self.rabbitmq(consumer=True, wait_threads=True) as (connection, consume_channel):
            self._basic_declare(consume_channel, queue_name)
            for (method, properties, body) in consume_channel.consume(queue=queue_name):
                if len(self.threads) > (max_number_threads or self.max_number_threads):
                    self._wait_threads()

                def go_two(): # RAN ON NEW THREAD
                    headers = properties.headers or {}
                    retry_count = int(headers.get('x-retry-count', 0))
                    delivery_tag = method.delivery_tag
                    def _resolve(): # threadsafe
                        connection.add_callback_threadsafe(partial(consume_channel.basic_ack, delivery_tag=delivery_tag))
                        self._exit_thread()

                    def _reject(requeue = True): # threadsafe
                        if requeue and retry_count < self.max_retries:
                            # re-publish the message with an incremented retry count
                            connection.add_callback_threadsafe(partial(self._basic_publish, consume_channel, queue_name, body, { **headers,  'x-retry-count': retry_count + 1 }, None))
                            self.logger.info("Requeued message: %r" % body)
                        _resolve() # Remove the message from RabbitMQ by acking it


                    callback(body, _reject, _resolve)

                t = threading.Thread(target=go_two)
                t.start()
                self.threads.append(t)

    # RabbitMQ Logic

    def _basic_declare(self, channel, queue_name):
        if queue_name in MAX_PRIORITIES:
            arguments = {"x-max-priority": MAX_PRIORITIES[queue_name]}
        else:
            arguments = None

        channel.queue_declare(queue=queue_name, arguments=arguments)

    def _basic_publish(self, channel, queue_name, body, headers, priority):
        channel.basic_publish(exchange='',
                                      routing_key=queue_name,
                                      body=body,
                                      properties=pika.BasicProperties(headers=headers,
                                                                      priority=priority))

    def _basic_purge(self, channel, queue_name):
        channel.queue_purge(queue_name)

    # RabbitMQ connection management

    @contextmanager
    def rabbitmq(self, wait_threads = False, consumer = False):
        """with self.rabbitmq() as (connnection, channel): pass"""
        cancel = consumer
        params = pika.ConnectionParameters(host=self.host,
                                           virtual_host=self.virtual_host,
                                           port=self.port,
                                           credentials=pika.PlainCredentials(username=self.username,
                                                                             password=self.password,
                                                                             erase_on_connect=True),
                                           heartbeat_interval=self.heartbeat_interval,
                                           connection_attempts=self.connection_attempts,
                                           backpressure_detection=self.backpressure_detection)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        self.active_connections.append(connection)
        try:
            yield (connection, channel)
        except pika.exceptions.ConsumerCancelled:
            self.logger.info("Consumer cancelled.")
            cancel = False
        except pika.exceptions.ConnectionClosedByBroker:
            self.logger.info("Broker cancelled")
            cancel = False
        finally:
            if wait_threads:
                swallow(self._wait_threads)
            if cancel:
                swallow(channel.cancel)
            swallow(channel.close)
            swallow(connection.close)
            self.active_connections.remove(connection)

    def _wait_threads(self, number=1000000):
        """Wait for min(number, len(self.threads)) threads to exit."""
        i = number
        while len(self.threads) > 0 and i > 0:
            for conn in self.active_connections:
                try:
                    conn.process_data_events(time_limit=0) # return as soon as possible.
                except:
                    pass

            try:
                thread_id = self.thread_queue.get_nowait()
            except queue.Empty:
                continue

            t = None
            for thread in self.threads:
                if thread.ident == thread_id:
                    t = thread
                    break

            # the thread has indicated that it's outlived it's usefulness, this will be quick.
            # It might not even be alive at this point!
            if t.is_alive():
                t.join()

            self.threads.remove(t)

            i -= 1

    def _exit_thread(self):
        """Indicate that a thread exited."""
        thread_id = threading.current_thread().ident
        self.thread_queue.put(thread_id)
