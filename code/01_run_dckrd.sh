#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

# Give children processes 5 minutes to timeout
env KILL_PROCESS_TIMEOUT=300
# Kill all other processes (such as those which have been forked)
env KILL_ALL_PROCESSES_TIMEOUT=300

FILE=/var/run/docker.pid
if test -f "$FILE"
then
    echo "$FILE exists; removing"
    rm $FILE

/usr/bin/dockerd --icc=true --log-level=info 2>&1 &
