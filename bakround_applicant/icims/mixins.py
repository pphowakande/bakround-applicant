__author__ = 'ajaynayak'

from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib.messages import error
from bakround_applicant.usage.utils import get_trial_days_remaining, get_subscription_plan_for_user


class SubscriptionRequiredMixin(AccessMixin):
    """
    CBV mixin which verifies that the current user is authenticated.
    """
    def dispatch(self, request, *args, **kwargs):
        if get_subscription_plan_for_user(request.user) is None and get_trial_days_remaining(request.user) < 0:
            error(request, 'Your trial has ended. Please choose a subscription to continue using Bakround.')
            return redirect('payment')
        return super(SubscriptionRequiredMixin, self).dispatch(request, *args, **kwargs)