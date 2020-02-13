__author__ = "natesymer"

## This class is an abstract class. Do not instantiate it directly.
#
# You can find reference NotificationFactory subclasses in .emails

import json
from django.template.loader import render_to_string
from bakround_applicant.services.queue import QueueConnection, QueueNames
from bakround_applicant.all_models.db import Notification

class NotificationFactory:
    def __init__(self):
        pass

    def notification_type(self, *args, **kwargs):
        """Return a str. Defaults to `email`."""
        return 'email'

    def generate_context(self, *args, **kwargs):
        """Return a dict, str => <ANYTHING>"""
        raise NotImplemented

    def generate_metadata(self, *args, **kwargs):
        """Return a dict of metadata."""
        return {}

    def pick_template(self, *args, **kwargs):
        """Return a template name (str). Then template should return a string
           that looks like <SUBJECT>\n<BODY>"""
        raise NotImplemented

    def postprocess(self, notification, *args, **kwargs):
        """Postprocess `notification`. Do not save! Either mutate or return a new one."""
        return notification

    def after_send(self, notification, *args, **kwargs):
        """Called after sending a notification"""
        pass

    def build(self, *args, **kwargs):
        context = self.generate_context(*args, **kwargs)
        template_name = self.pick_template(*args, **kwargs)
        typ = self.notification_type(*args, **kwargs)
        metadata = self.generate_metadata(*args, **kwargs)

        subject, body = render_to_string(template_name, context).split("\n", 1)

        n = Notification(subject=subject, body=body, type=typ, metadata=metadata)
        return self.postprocess(n, *args, **kwargs) or n

    def send(self, *args, **kwargs):
        n = self.build(*args, **kwargs)
        n.save()
        QueueConnection.quick_publish(QueueNames.notification_service,
                                      json.dumps({ 'notification_id': n.id }))
        self.after_send(n, *args, **kwargs)

