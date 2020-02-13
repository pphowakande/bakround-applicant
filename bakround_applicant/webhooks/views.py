__author__ = 'ajaynayak'

import json
import logging
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .utils import handle_email_event

# Called by SendGrid
@method_decorator(csrf_exempt, name='dispatch')
class HandleEmailEvent(View):

    @staticmethod
    def handle_request(received_json):
        if type(received_json) == list:
            for event in received_json:
                try:
                    handle_email_event(event)
                except:
                    logging.info(event)
                    logging.error("Unexpected error: ", exc_info=True)
                    pass
        else:
            handle_email_event(received_json)

        return

    def post(self, request):
        try:
            logging.info('Received a webhook from SendGrid: {}'.format(request.body.decode("utf-8")))
            received_json = json.loads(request.body.decode("utf-8"))
            self.handle_request(received_json)

            return HttpResponse(status=200)
        except:
            logging.error("Unexpected error: ", exc_info=True)

            return HttpResponse(status=500, content="Unexpected error")

