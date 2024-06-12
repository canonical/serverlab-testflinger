#!/bin/bash

profile=$1
NODE_NAME=$2
NODE_ID=$3
UPDATE_FILE_DIR=$PWD/UPDATES_NEEDED

usage(){
  echo "$0 maas_profile node_name node_id"
}

if [ "$#" -ne 3 ]; then
  echo "Incorrect number of args passed"
  echo
  usage
  exit 1
  fi
# copy files to PWD

if [[ -f "$PWD/sut/${NODE_NAME}.conf" && -f "$PWD/sut/${NODE_NAME}_snappy.conf" ]]; then
  echo "Files already exist in $PWD/sut"
else
    echo "Copying files to $PWD/sut"
    git mv $UPDATE_FILE_DIR/${NODE_NAME}* $PWD/sut/
fi

# fix the node id in the file
yq e ".node_id = \"$NODE_ID\"" -i ${PWD}/sut/${NODE_NAME}_snappy.yaml

# and make sure the maas user is updated
yq e ".maas_user = \"testflinger-maastiff\"" -i ${PWD}/sut/${NODE_NAME}_snappy.yaml

# verify maas connection and update storage if it works
if maas $profile version read &> /dev/null; then
    echo "MAAS connection verified, updating storage"
    $PWD/code/capture_node_storage.py --profile $profile --clear $PWD/sut/${NODE_NAME}_snappy.yaml
    $PWD/code/capture_node_storage.py --profile $profile --process $PWD/sut/${NODE_NAME}_snappy.yaml
else
    echo "MAAS connection failed, update storage later"
fi
