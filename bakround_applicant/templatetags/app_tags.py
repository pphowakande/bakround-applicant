__author__ = 'ajaynayak'

import os

from django import template
from bakround_applicant.usage.utils import get_subscription_plan_for_user, get_trial_days_remaining
from django.contrib.staticfiles.finders import find as find_static_file
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def relative_base():
    return mark_safe('<base href="' + os.environ['WEBSITE_ROOT_URL'] + '">')

@register.inclusion_tag('subscription_panel.html')
def get_subscription_panel(user):
    # trial_html = None
    # plan = get_subscription_plan_for_user(user)
    #
    # if plan is None:
    #     trial_days = get_trial_days_remaining(user)
    #     trial_html = "<span style='color: black; padding: 0px 10px 0px 5px'>(%s days remaining)</span>" % (trial_days if trial_days > -1 else 0)
    #
    # html = "<span style='color: black'>Plan: <span style='font-weight: bold'>%s</span></span>%s" % (plan if plan is not None else 'Best Fit Trial', trial_html)
    # return mark_safe(html)
    show_trial_message = False
    trial_days_remaining = 0
    plan = get_subscription_plan_for_user(user)

    if plan is None:
        show_trial_message = True
        trial_days_remaining = get_trial_days_remaining(user)

    return { "plan_name": plan if plan is not None else "Best Fit Trial",
                "trial_days_remaining": trial_days_remaining,
                "show_trial_message": show_trial_message
             }

