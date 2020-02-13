__author__ = 'ajaynayak'

from bakround_applicant.employer.models import Employer, EmployerUser
from bakround_applicant.event.models import Event
from .models import LookupPlanLimit, EmployerTrial
import logging
from django.utils import timezone
from bakround_applicant.utilities.helpers.dict import get_first_matching

from datetime import datetime, timedelta

from ..event import EventActions


def get_subscription_plan_for_user(user):
    employer_user = EmployerUser.objects.filter(user=user).first()

    if employer_user is None:
        return None

    return get_subscription_plan_for_employer(employer_user.id)


def get_subscription_plan_for_employer(employer_user_id):
    employer_user = EmployerUser.objects.get(pk=employer_user_id)
    if employer_user.is_billing_admin:
        return get_subscription_plan_from_billing_admin(employer_user.user_id)
    else:
        billing_admin = EmployerUser.objects.filter(employer_id=employer_user.employer_id,
                                                    is_billing_admin=True).first()
        if billing_admin is None:
            raise Exception('Billing admin for employer={} is not set.'.format(employer_user.employer_id))

        return get_subscription_plan_from_billing_admin(billing_admin.user_id)


def get_subscription_plan_from_billing_admin(billing_admin_user_id):
    return 'bestfit-trial'


def get_usage_limits_for_action(plan_name, action_name):
    plan_limit = LookupPlanLimit.objects.filter(plan_name=plan_name, action_name=action_name)\
                                                .order_by('id')\
                                                .first()

    if plan_limit is None:
        return None

    return plan_limit.limit


def get_action_count_by_employer(employer_id, action_name, current_day_only=False):
    user_ids = EmployerUser.objects.filter(employer_id=employer_id).values_list('user_id')
    events = Event.objects \
                 .filter(user_id__in=user_ids,
                         action=action_name)

    if current_day_only:
        events = events.filter(date_created__gte=datetime.now()-timedelta(days=1))

    return events.count()

def get_trial_days_remaining(user):
    employer_user = EmployerUser.objects.filter(user=user).first()

    if employer_user is None:
        return -1

    return get_employer_trial_days_remaining(employer_user.employer_id)


def get_employer_trial_days_remaining(employer_id):
    employer_trial = EmployerTrial.objects.filter(employer_id=employer_id)\
                                                .order_by('-date_created')\
                                                .first()
    if employer_trial is None:
        return -1

    time_delta = timezone.now() - employer_trial.date_created
    return employer_trial.trial_days - time_delta.days


def can_user_perform_action(user_id, action_name, action_count=1):
    employer_user = EmployerUser.objects.get(user_id=user_id)
    if employer_user.is_bakround_employee or employer_user.user.is_staff:
        return True

    plan = get_subscription_plan_for_employer(employer_user_id=employer_user.id)

    current_action_count = get_action_count_by_employer(employer_id=employer_user.employer_id,
                                                action_name=action_name,
                                                current_day_only=True)

    if action_name == EventActions.employer_job_candidate_contact \
            and not employer_user.is_bakround_employee \
            and (current_action_count >= 25 or current_action_count + action_count >= 25):
        return False

    if plan is None or (type(plan) == str and plan == 'bestfit-trial'):
        if get_employer_trial_days_remaining(employer_user.employer_id) < 0:
            return False
        plan_name = 'bestfit-trial'
    elif type(plan) == str:
        plan_name = plan
    else:
        plan_name = plan.plan

    plan_usage_limit = get_usage_limits_for_action(plan_name=plan_name, action_name=action_name)

    if plan_usage_limit is None:
        return True

    if plan_usage_limit < 1:
        return False

    total_action_count = get_action_count_by_employer(employer_id=employer_user.employer_id,
                                                action_name=action_name)

    return total_action_count <= plan_usage_limit or total_action_count + action_count <= plan_usage_limit


def get_plan_list():
    return []

def get_plan_by_id(plan_id):
    return None
