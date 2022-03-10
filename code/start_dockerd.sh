#!/bin/bash

FILE=/var/run/docker.pid

if test -f "$FILE"; then
    echo "$FILE exists; removing"
    rm $FILE
fi

/usr/bin/dockerd --icc=true --log-level=info 2>&1 &

sleep 5