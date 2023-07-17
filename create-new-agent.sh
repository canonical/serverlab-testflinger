#!/bin/bash


# Check if the number of arguments is 4
if [ $# -ne 4 ]; then
    echo "Error: The script requires exactly 4 arguments."
    echo "Usage: $0 <HOSTNAME> <MAAS_ID> <SECURE_ID> <IPADDR>"
    exit 1
fi

# Assign each argument to a specific variable
HOSTNAME="$1"
MAAS_ID="$2"
SECURE_ID="$3"
IPADDR="$4"

echo "Creating a new agent config using the following:"
echo "  Hostname is $HOSTNAME"
echo "  MAAS ID is $MAAS_ID"
echo "  SECURE ID is $SECURE_ID"
echo "  IP ADDRESS is $IPADDR"
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
server_address: https://testflinger.canonical.com:443
global_timeout: 172800
output_timeout: 43200
execution_basedir: /data/testflinger-agent/tests/$HOSTNAME/run
logging_basedir: /data/testflinger-agent/tests/$HOSTNAME/logs
results_basedir: /data/testflinger-agent/tests/$HOSTNAME/results
logging_level: INFO
job_queues:
  - anything
  - $HOSTNAME
setup_command: echo Setup
provision_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 provision -c /data/snappy-device-agents/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
test_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 runtest -c /data/snappy-device-agents/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
reserve_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 reserve -c /data/snappy-device-agents/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
cleanup_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 cleanup -c /data/snappy-device-agents/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json || /bin/true"
allocate_command: "PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 snappy-device-agent \
 maas2 allocate -c /data/snappy-device-agents/sut/${HOSTNAME}_snappy.yaml \
 testflinger.json"
EOF

# HOSTNAME.yaml
echo "  Creating sut/$HOSTNAME.yaml"
cat << EOF > sut/$HOSTNAME.yaml
job_queue: $HOSTNAME
provision_data:
 distro: focal
test_data:
 test_cmds: |
  ssh -o StrictHostKeyChecking=no ubuntu@$IPADDR ifconfig
EOF


# HOSTNAME_snappy.yaml
echo "  Creating sut/${HOSTNAME}_snappy.yaml"
cat << EOF > sut/"$HOSTNAME"_snappy.yaml
device_ip: $IPADDR
node_id: $MAAS_ID
node_name: $HOSTNAME
maas_user: testflinger_a
agent_name: $HOSTNAME
env:
 HEXR_DEVICE_SECURE_ID: $SECURE_ID
 DEVICE_IP: $IPADDR
EOF
