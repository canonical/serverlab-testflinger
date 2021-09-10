#!/bin/sh

echo
echo "###########################"
echo
echo "Starting SUT agents:"
echo

mkdir /var/log/tf-agent

for sutf in /data/testflinger-agent/sut/*; do
	if [ -f "$sutf" ]; then
		echo "$sutf"
		touch /var/log/tf-agent/${sutf%.*}
		testflinger-agent -c $sutf & > /var/log/tf-agent/${sutf%.*} 2>&1
		sleep .5
	fi
done

for logf in /var/log/tf-agent/*; do
	mv /var/log/tf-agent/$logf.conf


echo
echo "###########################"
echo