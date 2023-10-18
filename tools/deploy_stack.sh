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

docker-compose build \
  --build-arg ubuntu_scr=$UBUNTU_SCR \
  --build-arg host_dir=$PWD \
  --progress=tty 2>&1

# start stack
docker-compose up --detach 2>&1

python3 /opt/serverlab-testflinger/code/vault-template.py

# todo:
# add user input for pw?
