#!/usr/bin/env python3

from bakround_applicant.utilities.deployment import configure_django, is_local_env, DjangoServer, \
                                                    cpu_count, clear_caches, collect_static

configure_django(migrate=True, postgres=True)

# Perform Production-only tasks

if not is_local_env():
    clear_caches()
    collect_static()

# Start Django

DjangoServer().run()

