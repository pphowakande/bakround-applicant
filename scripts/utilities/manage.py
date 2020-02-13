#!/usr/bin/env python3
import os
import sys
from django.core.management import execute_from_command_line
from bakround_applicant.utilities.deployment import configure_django

if __name__ == '__main__':
    configure_django(postgres=True, default_local=True)
    execute_from_command_line(sys.argv)

