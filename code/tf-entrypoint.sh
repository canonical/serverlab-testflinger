#!/usr/bin/bash

echo "Logging into maas server..."

# MAAS_SERVER=10.245.128.4
# MAAS_PORT=5240
# MAAS_API_KEY="YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD"

# api key = final arg
/usr/bin/maas login testflinger_a http://10.245.128.4:5240/MAAS/ \
    YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD

# start init
/sbin/my_init -- bash -l