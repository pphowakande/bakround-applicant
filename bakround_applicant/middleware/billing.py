__author__ = 'ajaynayak'

from django.http import HttpResponse

from django.utils.deprecation import MiddlewareMixin

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve

import fnmatch

from bakround_applicant.usage.utils import get_trial_days_remaining, get_subscription_plan_for_user

EXEMPT = []

class SubscriptionPaymentMiddleware(MiddlewareMixin):
    """
    Used to redirect users from subcription-locked request destinations.

    Rules:

        * "(app_name)" means everything from this app is exempt
        * "[namespace]" means everything with this name is exempt
        * "namespace:name" means this namespaced URL is exempt
        * "name" means this URL is exempt
        * The entire djstripe namespace is exempt
        * If settings.DEBUG is True, then django-debug-toolbar is exempt
        * A 'fn:' prefix means the rest of the URL is fnmatch'd.

    Example::

        DJSTRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS = (
            "[blogs]",  # Anything in the blogs namespace
            "products:detail",  # A ProductDetail view you want shown to non-payers
            "home",  # Site homepage
            "fn:/accounts*",  # anything in the accounts/ URL path
        )
    """

    # def process_exception(self, request, exception):
    #     print(exception)
    #     return HttpResponse("in exception")

    def process_request(self, request):
        """Check the subscriber's subscription status.

        Returns early if request does not outlined in this middleware's docstring.
        """
        if self.is_matching_rule(request):
            return

        return self.check_subscription(request)

    def is_matching_rule(self, request):
        #print(request)
        """Check according to the rules defined in the class docstring."""
        # First, if in DEBUG mode and with django-debug-toolbar, we skip
        #   this entire process.
        if settings.DEBUG and request.path.startswith("/__debug__"):
            return True

        # Second we check against matches
        match = resolve(request.path, None)#request.resolver_match.url_name)#request.urlconf)
        if "({0})".format(match.app_name) in EXEMPT:
            return True

        if "[{0}]".format(match.namespace) in EXEMPT:
            return True

        if "{0}:{1}".format(match.namespace, match.url_name) in EXEMPT:
            return True

        if match.url_name in EXEMPT:
            return True

        # Third, we check wildcards:
        for exempt in [x for x in EXEMPT if x.startswith('fn:')]:
            exempt = exempt.replace('fn:', '')
            #print('{} {}', request.path, exempt)
            if fnmatch.fnmatch(request.path, exempt):

                return True


        return False

    def check_subscription(self, request):
        """Redirect to the subscribe page if the user lacks an active subscription."""

        if not request.user or not request.user.is_authenticated():
            return redirect("account_login")

