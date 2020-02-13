__author__ = "natesymer"

import json

from bakround_applicant.utilities.logger import LoggerFactory
from bakround_applicant.all_models.db import ProfileVerificationRequest
from bakround_applicant.services.queue import QueueNames, QueueConnection

verif_logger = LoggerFactory.create("request_verification_for()")
def request_verification_for(profile_id, callback_queue = None, callback_message = None, metadata = {}, force_reverification = False):
    verif_logger.info("Building ProfileVerificationRequest for Profile id {}...".format(profile_id))

    rq = ProfileVerificationRequest.objects.filter(profile_id=profile_id).first()
    if not rq:
        rq = ProfileVerificationRequest(profile_id=profile_id, use_manual=False)
    else:
        verif_logger.info("Profile id {} already has a ProfileVerificationRequest (id {})".format(profile_id, rq.id))

    rq.verified = False
    rq.metadata = metadata

    if 'bkrnd_ecid' in rq.metadata:
        verif_logger.info("Profile id {} is linked to EmployerCandidate id {}.".format(profile_id, metadata['bkrnd_ecid']))
    else:
        verif_logger.info("Profile id {} is not linked to any EmployerCandidate.".format(profile_id))

    if callback_message and callback_queue:
        rq.callback_queue = callback_queue
        rq.callback_message = json.dumps(callback_message)
        verif_logger.info("Successful verification of Profile id {} will publish a message on {}".format(profile_id, rq.callback_queue))

    rq.save()

    if not rq.use_manual:
        QueueConnection.quick_publish(queue_name=QueueNames.verifying_service,
                                      body=json.dumps({ 'request_id': rq.id,
                                                        'force_reverification': force_reverification }))

def queue_request(pvr):
    QueueConnection.quick_publish(queue_name=QueueNames.verifying_service,
                                      body=json.dumps({ 'request_id': pvr.id,
                                                        'force_reverification': True }))

