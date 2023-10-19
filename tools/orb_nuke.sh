#!/usr/bin/bash

docker stop $(docker ps -a -q)

docker rm -vf $(docker ps -a -q)

docker rmi -f $(docker images -a -q)

# docker volume rm -f $(docker volume ls -q)

docker volume rm -f $(docker volume ls -q | grep -v serverlab-testflinger_vault_data)

docker network prune -f

docker builder prune -a -f


# docker stop $(docker ps -a --format '{{.Names}}' | grep -v 'nh-vault' | xargs -I {} docker ps -q -f name={})

# docker rm -vf $(docker ps -a --format '{{.Names}}' | grep -v 'nh-vault' | xargs -I {} docker ps -q -f name={})

# docker rmi -f $(docker ps -a --format '{{.Names}}' | grep -v 'nh-vault' | xargs -I {} docker ps -q -f name={})

# docker volume rm -f $(docker volume ls -q | grep -v testflinger-docker_vault_data)

# docker builder prune -a -f
