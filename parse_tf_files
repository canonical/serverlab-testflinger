#!/usr/bin/bash

shopt -s extglob

# replicate authorized_keys
cp ~/.ssh/authorized_keys ./ssh/
chmod 644 ./ssh/authorized_keys

# copy tf-agent files
AGENT="sut/!(*snappy*).conf"
cp $AGENT sut/agent/

# copy snappy-agent files
SNAPPY="sut/*snappy*.y*ml"
cp $SNAPPY sut/snappy/

# copy tf-cli files
CLI="sut/!(*snappy*).y*ml"
cp $CLI sut/cli/
