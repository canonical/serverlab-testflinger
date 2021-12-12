#!/usr/bin/bash

export MAAS_HOST=10.245.128.4
export MAAS_PORT=5240
export MAAS_API_KEY='YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD'
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# temp pws
UBUNTU_SCR=ch4ng3m3
TESTFLINGER_SCR=u24xeO6EKuWt

docker stop $(docker ps -a -q)
docker rm -vf $(docker ps -a -q)
docker rmi -f $(docker images -a -q)
docker volume rm -f $(docker volume ls -q)
docker network prune -f
docker builder prune -a -f

docker-compose build \
  --build-arg ubuntu_scr=$UBUNTU_SCR \
  --build-arg testflinger_scr=$TESTFLINGER_SCR \
  --progress=tty \
  --no-cache \
  --force-rm 2>&1

# start stack
docker-compose up --detach 2>&1

# todo:
# add user input for pw?
