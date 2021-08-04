#!/usr/bin/bash

ubuntu_scr=ch4ng3m3
testflinger_scr=u24xeO6EKuWt
maas_api_key='YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD'
maas_host=10.245.128.4
maas_port=5240

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker-compose build \
  --build-arg ubuntu_scr=$ubuntu_scr \
  --build-arg testflinger_scr=$testflinger_scr \
  --build-arg maas_api_key=$maas_api_key \
  --build-arg maas_host=$maas_host \
  --build-arg maas_port=$maas_port \
  --progress=tty \
  --no-cache \
  --force-rm 2>&1

# start stack
docker-compose up --detach 2>&1

# todo:
# add user input for pw?
