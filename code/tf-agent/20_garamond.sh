#!/bin/sh

sut="garamond"

echo "* starting agent: $sut"
touch /var/log/tf-agent/$sut

testflinger-agent -c /data/testflinger-agent/sut/$sut.conf >> /var/log/tf-agent/$sut
sleep .5