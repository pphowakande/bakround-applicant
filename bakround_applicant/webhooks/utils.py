__author__ = 'ajaynayak'

from bakround_applicant.all_models.db import ProfileEmail
from bakround_applicant.utilities.functions import get_website_root_url
import requests

def handle_email_event(json_event, save_events = False):
    # if the request is for a different environment (ie. dev or local), route it to the appropriate environment endpoint
    if 'bkrnd_url' in json_event and get_website_root_url() not in json_event['bkrnd_url']:
        modified_json = json_event
        modified_json['bkrnd_url'] = None

        r = requests.post('{}/webhooks/handle_email_event'.format(json_event['bkrnd_url']),
                          data=modified_json)
        if r.status_code == 200:
            return
        else:
            raise Exception('Unable to redirect an email event to {}.'.format(json_event['bkrnd_url']))

    if 'sg_event_id' not in json_event or 'event' not in json_event or 'email' not in json_event:
        raise Exception('Unable to extract the relevant fields from the request.')

    sg_event_id = json_event['sg_event_id']
    event = json_event['event']
    email = json_event['email']

    update_email_status_from_sendgrid(email, event)

def update_email_status_from_sendgrid(email_str, event):
    qs = ProfileEmail.objects.filter(value=email_str)

    if event == 'bounce' or event == 'dropped':
        qs.update(bounces=True)
    elif event == 'delivered':
        qs.update(bounces=False)
    elif event == 'open':
        qs.update(opens=True, bounces=False)
    elif event == 'unsubscribe' or event == 'group_unsubscribe':
        qs.update(unsubscribed=True)
    elif event == 'group_resubscribe':
        qs.update(unsubscribed=False)
    elif event == 'spamreport':
        qs.update(reported_spam=True)
    elif event == 'click':
        qs.update(responds=True, bounces=False)
