#!/usr/bin/bash

UBUNTU_SCR=ch4ng3m3
TESTFLINGER_SCR=u24xeO6EKuWt

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

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
