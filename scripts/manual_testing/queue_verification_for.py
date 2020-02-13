#!/usr/bin/python3

# queues a profile to be automatically verified
# ./queue_verification_for.py <profile_id>

import sys
import os
import importlib
import time
import json

from bakround_applicant.utilities.deployment import configure_django
from bakround_applicant.services.queue import QueueConnection, QueueNames
from bakround_applicant.all_models.db import Profile, ProfileVerificationRequest

if __name__ == '__main__':
    configure_django(rabbitmq=True, postgres=True, default_local=True)

    profile_id = int(sys.argv[1])
    if not Profile.objects.filter(id=profile_id).first():
        print("Profile id {} does not exist.".format(profile_id))
        sys.exit(1)

    rq = ProfileVerificationRequest.objects.filter(profile_id=profile_id).first()
    if not rq:
        rq = ProfileVerificationRequest(profile_id=profile_id)

    rq.use_manual = False
    rq.save()

    QueueConnection().publish(queue_name=QueueNames.verifying_service, body=json.dumps({ 'request_id': rq.id }))

    print("Queued Profile id {} (ProfileVerificationRequest id {}).".format(profile_id, rq.id))

