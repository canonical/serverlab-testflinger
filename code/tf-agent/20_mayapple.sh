#!/bin/sh

sut="mayapple"

echo "* starting agent: $sut"
touch /var/log/tf-agent/$sut

nohup testflinger-agent -c /data/testflinger-agent/$sut &> /var/log/tf-agent/$sut
sleep .5