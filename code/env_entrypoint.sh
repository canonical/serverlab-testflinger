#!/usr/bin/bash

# get your envs files and export envars
export $(egrep  -v '^#'  /run/secrets/* | xargs) 
# if you need some specific file, where password is the secret name 
# export $(egrep  -v '^#'  /run/secrets/password| xargs) 
# call the dockerfile's entrypoint
source /opt/tf-entrypoint.sh