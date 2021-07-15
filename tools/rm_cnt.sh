#!/usr/bin/bash

docker stop $(docker ps -a -q)
docker rm -vf $(docker ps -a -q)

