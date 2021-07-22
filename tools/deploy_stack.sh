#!/usr/bin/bash

export DOCKER_BUILDKIT=1

secrets_file=./.tfscr

# docker-compose build does not support build secrets (in dev)
# therefore, we must use discrete docker build cmds
docker build -t redis \
  --progress=plain \
  .  2>&1
docker build -f testflinger-api \
  -t python:3.8-slim-buster \
  --progress=plain \
  .  2>&1
docker build -f testflinger-agent \
  -t phusion/baseimage:focal-1.0.0 \
  --secret id=tf_secret,src=$secrets_file \
  --progress=plain \
  .  2>&1
docker build -f testflinger-cli \
  -t phusion/baseimage:focal-1.0.0 \
  --secret id=tf_secret,src=$secrets_file \
  --progress=plain \
  .  2>&1

# start stack
docker-compose start --detach 2>&1

# rm $secrets_file

# todo:
# add user input for pw, echo to file and rm at eof?