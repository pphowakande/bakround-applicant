#!/bin/sh

/remote_syslog2 \
  --dest-host $PAPERTRAIL_HOST \
  --dest-port $PAPERTRAIL_PORT \
  --hostname $PAPERTRAIL_HOSTNAME \
  --no-detach \
  --new-file-check-interval 1 \
  /var/log/\*.log

