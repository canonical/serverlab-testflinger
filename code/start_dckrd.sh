#!/bin/bash

function cleanup()
{
    ps -ef | grep 'dockerd' | grep -v grep | \
      awk '{print $2}' | xargs -r kill -9
    sleep 2
    ps -ef | grep 'containerd' | grep -v grep | \
      awk '{print $2}' | xargs -r kill -9
    sleep 2

    FILE=/var/run/docker.pid
    if test -f "$FILE"; then
        echo "$FILE exists; removing"
        rm $FILE
    fi
}

# /bin/bash -c set -e && /usr/bin/dockerd --icc=true --log-level=info 2>&1
if ! pgrep dockerd
then
    trap cleanup EXIT SIGHUP SIGINT SIGQUIT SIGTERM

    # if pgrep containerd
    # then
    #     pkill -f containerd
    #     sleep 4
    #     pkill sshd
    # fi

    FILE=/var/run/docker.pid
    if test -f "$FILE"
    then
        echo "$FILE exists; removing"
        rm $FILE
    fi

    /usr/bin/dockerd --icc=true --log-level=info 2>&1
    # wait for api to load
    sleep 3
else
    echo " * dockerd running... "
fi