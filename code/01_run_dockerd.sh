#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

echo "###########################"
echo "Starting Docker daemon"
exec /opt/start_dockerd.sh 2>&1 &