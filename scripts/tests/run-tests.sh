#!/bin/sh
# This should only be run from inside docker-compose.
# To run outside, run:  make test

cd bakround_applicant
pytest --no-migrations $*
