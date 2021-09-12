#!/bin/sh

sut="meitner"

echo "* starting agent: $sut"
touch /var/log/tf-agent/$sut

nohup testflinger-agent -c /data/testflinger-agent/sut/$sut.conf &> /var/log/tf-agent/$sut
sleep .5