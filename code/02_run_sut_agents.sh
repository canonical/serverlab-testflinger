#!/bin/sh
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

exec python3 /opt/init_agent_cntnrs.py 2>&1 &