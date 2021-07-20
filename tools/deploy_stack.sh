#!/usr/bin/bash

COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
docker-compose up --detach --secret id=ubuntu,src=/secrets/ubuntu \
--secret id=testflinger,src=/secrets/testflinger