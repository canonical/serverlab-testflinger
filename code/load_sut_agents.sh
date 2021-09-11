#!/bin/sh
echo
echo
echo "###########################"
echo
echo "Starting SUT agents:"
echo

# check if exists
mkdir /var/log/tf-agent

cd /data/testflinger-agent/sut

for sutf in *; do
	if [ -f "$sutf" ]; then
		echo "$sutf"
		touch /var/log/tf-agent/${sutf%.*}
		nohup PYTHONIOENCODING=utf-8 testflinger-agent -c $sutf &> /var/log/tf-agent/${sutf%.*} &
		sleep .5
	fi
done

echo
echo "###########################"
