#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

FILE=/var/run/docker.pid

echo "###########################"
echo "Sanitizing environment..."

/usr/bin/pkill -f dockerd
sleep 8
/usr/bin/pkill -f containerd
sleep 3

if test -f "$FILE"; then
    echo "$FILE exists; removing"
    rm $FILE
fi

echo "Starting Docker daemon"
/bin/bash -c set -e && /usr/bin/dockerd --icc=true --log-level=info 2>&1 &

sleep 3