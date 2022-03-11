#!/bin/bash
# `/sbin/setuser memcache` runs the given command as the user `memcache`.
# If you omit that part, the command will be run as root.

# Give children processes 5 minutes to timeout
env KILL_PROCESS_TIMEOUT=300
# Kill all other processes (such as those which have been forked)
env KILL_ALL_PROCESSES_TIMEOUT=300

if ! pgrep containerd
then
    if ! pgrep dockerd
    then
        FILE=/var/run/docker.pid
        if test -f "$FILE"
        then
            echo "$FILE exists; removing"
            rm $FILE
    fi

    /usr/bin/dockerd --icc=true --log-level=info 2>&1 &
    # /opt/start_dckrd.sh &
    # wait for api to load
    sleep 3
else
    echo '* dockerd running...'
fi