__author__ = 'ajaynayak'

import time
import html
from django.views import View
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .logic import get_stats
from .new_users import get_new_user_stats


def send_profile_stats_email():
    stats_text = get_stats()
    stats_html = "<pre>" + html.escape(stats_text) + "</pre>"
    todays_date = time.strftime("%B %d, %Y")

    send_mail(subject="Profile stats as of {}".format(todays_date),
              message=stats_text,
              html_message=stats_html,
              from_email="noreply@bakround.com",
              recipient_list=["stats@bakround.com"])


def send_new_user_stats_email():
    stats_text = get_new_user_stats()
    stats_html = "<pre>" + html.escape(stats_text) + "</pre>"
    todays_date = time.strftime("%B %d, %Y")

    send_mail(subject="New user stats for {}".format(todays_date),
              message=stats_text,
              html_message=stats_html,
              from_email="noreply@bakround.com",
              recipient_list=["stats@bakround.com"])
