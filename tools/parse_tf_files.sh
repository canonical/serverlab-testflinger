#!/usr/bin/bash

shopt -s extglob

# replicate authorized_keys
mkdir ./ssh
cp ~/.ssh/authorized_keys ./ssh/
chmod 644 ./ssh/authorized_keys

# copy tf-agent files
AGENT="sut/!(*snappy*).conf"
mkdir ./sut/agent
cp $AGENT sut/agent/

# copy snappy-agent files
SNAPPY="sut/*snappy*.y*ml"
mkdir ./sut/snappy
cp $SNAPPY sut/snappy/

# copy tf-cli files
CLI="sut/!(*snappy*).y*ml"
mkdir ./sut/cli
cp $CLI sut/cli/
