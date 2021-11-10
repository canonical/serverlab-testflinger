#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

# exec > >(/sbin/setuser ubuntu nohup python3 /opt/start_sut_agents.py 2>&1 &)

exec /sbin/setuser ubuntu python3 /opt/start_sut_agents.py 2>&1 &