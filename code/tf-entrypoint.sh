#!/usr/bin/bash

source /opt/serverlab-testflinger/config.sh

# these values can be overriden with exec (VAR='value' ./tf-entrypoint.sh)
: ${TF_MAAS_ACT:=$TF_MAAS_ACT}
: ${MAAS_HOST:=$MAAS_HOST}
: ${MAAS_PORT:=5240}
: ${MAAS_API_KEY:=$MAAS_API_KEY}

echo
echo "###########################"
echo
echo "Logging into maas server..."
/usr/bin/maas login $TF_MAAS_ACT http://$MAAS_HOST:$MAAS_PORT/MAAS/ $MAAS_API_KEY

echo "Replicating maas-cli db..."
cp /root/.maascli.db /home/ubuntu/
# cp /root/.maascli.db /home/testflinger/
chown ubuntu:ubuntu /home/ubuntu/.maascli.db
# chown testflinger:testflinger /home/testflinger/.maascli.db

echo
echo "Exporting ssh pubkeys..."
echo "- User: root"
/opt/export_ssh_pubkey.py --path /root/ \
                          --mapi $MAAS_API_KEY \
                          --mhost $MAAS_HOST \
                          --mport $MAAS_PORT
echo
echo "Exporting ssh pubkeys..."
echo "- User: ubuntu"
/opt/export_ssh_pubkey.py --path /home/ubuntu/ \
                          --mapi $MAAS_API_KEY \
                          --mhost $MAAS_HOST \
                          --mport $MAAS_PORT

# echo
# echo "- User: testflinger"
# /opt/export_ssh_pubkey.py --path /home/testflinger/ \
#                           --mapi $MAAS_API_KEY \
#                           --mhost $MAAS_HOST \
#                           --mport $MAAS_PORT
# echo

echo
echo "###########################"
echo
echo "Starting init.d and /etc/my_init services..."

# start init
echo
echo "Starting my_initd..."
/sbin/my_init -- bash -l
