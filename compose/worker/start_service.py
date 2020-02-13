#!/usr/bin/env python3

import sys
import importlib

if len(sys.argv) < 2:
    raise Exception("You must provide a service name as the argument.")

from bakround_applicant.utilities.deployment import configure_django

# Historically, migrations were never ran here. Should this change?
# Probably, since new code will be ran almost as soon as RabbitMQ is
# up and connected.
# However, someone might have ran into problems doing so, and just
# stopped doing it.
configure_django(postgres=True, rabbitmq=True)

consumer_module_name = 'bakround_applicant.services.{}.consumer'.format(sys.argv[1])
consumer_module = importlib.import_module(consumer_module_name)
consumer_module.Consumer().consume()

