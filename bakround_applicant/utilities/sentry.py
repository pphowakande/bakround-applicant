__author__ = "natesymer"

import os
import traceback

import raven

from bakround_applicant.utilities.functions import is_production

sentry_client = None
if 'SENTRY_DSN' in os.environ:
    try:
        sentry_client = raven.Client(os.environ['SENTRY_DSN'])
    except:
        pass

def forward_exception_to_sentry():
    if is_production():
        try:
            sentry_client.captureException()
            return
        except:
            pass

    print(traceback.format_exc())
