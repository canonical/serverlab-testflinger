#!/usr/bin/bash

docker stop $(docker ps -a -q)

docker rm -vf $(docker ps -a -q)

docker rmi -f $(docker images -a -q)

docker volume rm -f $(docker volume ls -q)

docker network prune -f

docker builder prune -a -f

sleep 1

git pull

sleep 1

./tools/deploy_stack.sh