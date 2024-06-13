#!/bin/bash

profile=$1
NODE_NAME=$2
NODE_ID=$3
UPDATE_FILE_DIR=$PWD/UPDATES_NEEDED


usage(){
    echo "$0 maas_profile node_name (node_id)"
    echo "node_id is optional, if not supplied, it will be fetched from MAAS"
    echo 
    echo "This script was created to quickly fix agent configs that needed modifications"
    echo "due to having to rebuild the maas environment.  Leaving it in the tree for legacy"
    echo "reasons, but it is not recommended to use this script for new work."
}

if [ "$#" -ne 2 ]; then
  echo "Incorrect number of args passed"
  usage
  exit 1
fi

if [ -z "$NODE_ID" ]; then
    echo "No node_id supplied, fetching from MAAS"
    NODE_ID=$(maas $profile machines read | jq -r --arg HOSTNAME "$NODE_NAME" '.[] | select(.hostname == $HOSTNAME) | .system_id')
    if [ -z "$NODE_ID" ]; then
        echo "No node_id found in MAAS, exiting"
        echo "You can supply the node_id as the third argument"
        exit 1
    fi
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
