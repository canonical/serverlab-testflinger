#!/bin/sh
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

exec /sbin/setuser ubuntu python3 /opt/start_sut_agents.py 2>&1 &