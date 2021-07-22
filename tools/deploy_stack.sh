#!/usr/bin/bash

export DOCKER_BUILDKIT=1

docker build -f testflinger-db
docker build -f testflinger-api
docker build -f testflinger-agent \
	--secret id=ubuntu_secret id=testflinger_secret \
	--progress=plain \
docker build -f testflinger-cli \
	--secret id=ubuntu_secret id=testflinger_secret \
	--progress=plain \
docker-compose start --detach 2>&1