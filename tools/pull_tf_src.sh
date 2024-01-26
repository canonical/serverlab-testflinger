#!/usr/bin/bash

mkdir ./src
cd ./src

git clone https://git.launchpad.net/testflinger
#git clone https://git.launchpad.net/testflinger-agent
#git clone https://git.launchpad.net/testflinger-cli
#git clone https://git.launchpad.net/snappy-device-agents

cp ../code/testflinger.conf ./testflinger/server/testflinger.conf
cp ../code/testflinger-agent.conf ./testflinger/agent/testflinger-agent.conf
