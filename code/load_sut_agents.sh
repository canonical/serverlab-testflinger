#!/bin/sh

echo
echo "###########################"
echo
echo "Starting SUT agents:"
echo

for sutf in /data/testflinger-agent/sut/*; do
	if [ -f "$sutf" ]; then
		echo "$sutf"
		testflinger-agent -c $sutf &
		sleep 1.5
	fi
done

echo
echo "###########################"
echo