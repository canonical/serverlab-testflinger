#!/bin/bash

FILE=/var/run/docker.pid

/usr/bin/pkill -f dockerd

if test -f "$FILE"; then
    echo "$FILE exists; removing"
    rm $FILE
fi

/usr/bin/dockerd --icc=true --log-level=info 2>&1 &

sleep 3