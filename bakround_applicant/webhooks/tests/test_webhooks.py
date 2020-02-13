__author__ = 'ajaynayak'

import pytest
import os
import json
from django.conf import settings
from ..utils import handle_email_event
from bakround_applicant.services.verifyingservice.util import add_contact
from bakround_applicant.all_models.db import NotificationRecipientEvent, NotificationRecipient, Notification, ProfileEmail, Profile

@pytest.mark.django_db
def test_email_events():
    notification = Notification(type='email', sent=True)
    notification.save()

    events = json.loads(open(os.path.join(str(settings.APPS_DIR), "webhooks/tests/sendgrid_webhooks.json"), 'r').read())

    for event in events:
        event['bkrnd_nid'] = notification.id
        notification_recipient = NotificationRecipient(notification=notification,
                                                       recipient_email=event['email'],
                                                       sent=True)
        notification_recipient.save()
        p = Profile()
        p.save()
        pe = add_contact(ProfileEmail, event["email"], p.id)

        handle_email_event(event, save_events = True)

        saved_item = NotificationRecipientEvent.objects.filter(action=event['event']).first()
        assert saved_item
        assert saved_item.sg_event_id == event['sg_event_id']
        assert saved_item.notification_recipient is not None
        assert saved_item.notification_recipient.notification_id == notification.id

        pe = ProfileEmail.objects.filter(id=pe.id).first()
        assert pe

        if event['event'] == 'bounce':
            assert pe.bounces

        if event['event'] == 'bounce':
            assert len(ProfileEmail.objects.filter(value=event['email'], bounces=True)) > 0


