#!/bin/bash

usage() {
    echo "Usage: $0 <HOSTNAME> <CID> <SECURE_ID> <IPADDR> <MAAS_PROFILE> <MAAS_ID>"
    echo "HOSTNAME: The hostname of the device in MAAS"
    echo "CID: The unique C3 identifier for the device"
    echo "SECURE_ID: The secure ID for the device from C3"
    echo "IPADDR: The IP address of the device"
    echo "MAAS_PROFILE: The MAAS profile to use to access MAAS to get certain data"
    echo "MAAS_ID: The MAAS node_id for the device"
    exit 1
}

# Check if the number of arguments is 4
if [ $# -ne 5 ]; then
    usage
fi

# Assign each argument to a specific variable
HOSTNAME="$1"
CID="$2"
SECURE_ID="$3"
IPADDR="$4"
MAAS_USER="$5"
MAAS_ID="$6"

if [ -z "$MAAS_ID" ]; then
    echo "No node_id supplied, fetching from MAAS"
    MAAS_ID=$(maas $MAAS_USER machines read | jq -r --arg HOSTNAME "$HOSTNAME" '.[] | select(.hostname == $HOSTNAME) | .system_id')
    if [ -z "$MAAS_ID" ]; then
        echo "No node_id found in MAAS, exiting"
        echo "You can supply the node_id as the last argument"
        usage
        exit 1
    fi
fi

echo "Creating a new agent config using the following:"
echo "  Hostname is $HOSTNAME"
echo "  CID is $CID"
echo "  MAAS ID is $MAAS_ID"
echo "  SECURE ID is $SECURE_ID"
echo "  IP ADDRESS is $IPADDR"
echo "  MAAS PROFILE is $MAAS_USER"
echo
read -p "Y/y to continue, N/n to exit " KEEP_GOING
KEEP_GOING="${KEEP_GOING,,}"
if [ "$KEEP_GOING" == "y" ]; then
    echo "Creating files now..."
else
    exit 0
fi

# HOSTNAME.conf
echo "  Creating sut/$HOSTNAME.conf"
cat << EOF > sut/$HOSTNAME.conf
agent_id: $HOSTNAME
identifier: $CID
provision_type: maas2
server_address: https://testflinger.canonical.com:443
global_timeout: 172800
output_timeout: 43200
execution_basedir: /data/testflinger/agent/tests/$HOSTNAME/run
logging_basedir: /data/testflinger/agent/tests/$HOSTNAME/logs
results_basedir: /data/testflinger/agent/tests/$HOSTNAME/results
logging_level: INFO
job_queues:
  - anything
  - $HOSTNAME
  - $CID
setup_command: echo Setup
provision_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 provision -c /data/testflinger/device-connectors/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
test_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 runtest -c /data/testflinger/device-connectors/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
reserve_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 reserve -c /data/testflinger/device-connectors/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
cleanup_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 cleanup -c /data/testflinger/device-connectors/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json || /bin/true"
allocate_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 allocate -c /data/testflinger/device-connectors/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
EOF

# HOSTNAME_snappy.yaml
echo "  Creating sut/${HOSTNAME}_snappy.yaml"
cat << EOF > sut/"$HOSTNAME"_snappy.yaml
device_ip: $IPADDR
node_id: $MAAS_ID
node_name: $HOSTNAME
maas_user: testflinger-maastiff
agent_name: $HOSTNAME
max_reserve_timeout: 604800
env:
 HEXR_DEVICE_SECURE_ID: $SECURE_ID
 DEVICE_IP: $IPADDR
EOF

# verify maas connection and update storage if it works
if maas $MAAS_USER version read &> /dev/null; then
    echo "MAAS connection verified, updating storage"
    $PWD/code/capture_node_storage.py --profile $MAAS_USER --clear $PWD/sut/${HOSTNAME}_snappy.yaml
    $PWD/code/capture_node_storage.py --profile $MAAS_USER --process $PWD/sut/${HOSTNAME}_snappy.yaml
else
    echo "MAAS connection failed, update storage later"
fi

