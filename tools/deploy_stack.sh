#!/usr/bin/bash
# Must be run from Docker root (compose.yaml,etc)

export MAAS_HOST=10.245.128.4
export MAAS_PORT=5240
export MAAS_API_KEY='YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD'
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# temp pws
UBUNTU_SCR=ch4ng3m3
# TESTFLINGER_SCR=u24xeO6EKuWt
INFLUX_HOST="10.245.128.9"
INFLUX_PORT="8086"
INFLUX_USER="root"
INFLUX_PW="root"

docker-compose build \
  --build-arg ubuntu_scr=$UBUNTU_SCR \
  --build-arg host_dir=$PWD \
  --build-arg host_dir=$INFLUX_HOST \
  --build-arg host_dir=$INFLUX_PW \
  --build-arg host_dir=$INFLUX_USER \
  --build-arg host_dir=$INFLUX_PORT \
  --progress=tty 2>&1

# start stack
docker-compose up --detach 2>&1

# todo:
# add user input for pw?
