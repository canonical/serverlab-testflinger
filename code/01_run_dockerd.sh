#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

FILE=/var/run/docker.pid

echo "###########################"
echo "Starting Docker daemon"

if test -f "$FILE"; then
    echo "$FILE exists; removing"
    rm $FILE
fi

/usr/bin/dockerd --icc=true --log-level=info 2>&1 &

sleep 3