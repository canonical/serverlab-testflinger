#!/usr/bin/bash

# these values can be overriden with exec (VAR='value' ./tf-entrypoint.sh)
: ${TF_MAAS_ACT:=testflinger_a}
: ${MAAS_HOST:=10.245.128.4}
: ${MAAS_PORT:=5240}
: ${MAAS_API_KEY:='YQg7utpEbD5sZ5jyPP:frwtnUJbXReMtfZxtz:vnAAt9zrGZPxNKEGRyp76Eku5nedq2xD'}

echo
echo "###########################"
echo
echo "Logging into maas server..."
/usr/bin/maas login $TF_MAAS_ACT http://$MAAS_HOST:$MAAS_PORT/MAAS/ $MAAS_API_KEY

echo "Replicating maas-cli db..."
cp /root/.maascli.db /home/ubuntu/
cp /root/.maascli.db /home/testflinger/
chown ubuntu:ubuntu /home/ubuntu/.maascli.db
chown testflinger:testflinger /home/testflinger/.maascli.db

echo
echo "Exporting ssh pubkeys..."
echo "- User: ubuntu"
/opt/export_ssh_pubkey.py --path /home/ubuntu/ \
                          --mapi $MAAS_API_KEY \
                          --mhost $MAAS_HOST \
                          --mport $MAAS_PORT
echo
echo "- User: testflinger"
/opt/export_ssh_pubkey.py --path /home/testflinger/ \
                          --mapi $MAAS_API_KEY \
                          --mhost $MAAS_HOST \
                          --mport $MAAS_PORT
echo

# start sut agents (tf-agent only)
if test -f "/opt/start_sut_agents.py"; then
    # facilitate sut-agent logging
    mkdir /var/log/sut-agent
    chown testflinger:testflinger /var/log/sut-agent
    sudo -u testflinger /usr/bin/python3 /opt/start_sut_agents.py
fi

echo
echo "###########################"
echo
echo "Starting init.d and /etc/my_init services..."

# start init
/sbin/my_init -- bash -l
