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
INFLUX_HOST=10.245.128.9
INFLUX_PORT=8086
INFLUX_USER=root
INFLUX_PW=root

docker-compose build \
  --build-arg ubuntu_scr=$UBUNTU_SCR \
  --build-arg host_dir=$PWD \
  --build-arg influx_host=$INFLUX_HOST \
  --build-arg influx_pw=$INFLUX_PW \
  --build-arg influx_user=$INFLUX_USER \
  --build-arg influx_port=$INFLUX_PORT \
  --progress=tty 2>&1

# start stack
docker-compose up --detach 2>&1

# todo:
# add user input for pw?
