#!/bin/bash

NODE_NAME=$1
NODE_ID=$2
UPDATE_FILE_DIR=$PWD/UPDATES_NEEDED

# copy files to PWD

git mv $UPDATE_FILE_DIR/$NODE_NAME* $PWD/sut/

# fix the node id in the file

yq e ".node_id = \"$NODE_ID\"" -i ${PWD}/sut/${NODE_NAME}_snappy.yaml

# and make sure the maas user is updated
yq e ".maas_user = \"testflinger-maastiff\"" -i ${PWD}/sut/${NODE_NAME}_snappy.yaml

