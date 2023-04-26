#!/bin/sh
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

export INFLUX_HOST="10.245.128.9" \
  && export INFLUX_PORT="8086" \
  && export INFLUX_USER="root" \
  && export INFLUX_PW="root"