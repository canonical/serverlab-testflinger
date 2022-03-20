#!/usr/bin/python3

import paho.mqtt.subscribe as subscribe
import platform
import sys
# user agent checks


def check_status(client, userdata, message):
    message = (message.payload).decode('UTF-8')
    if 'offline' in message:
        # report unhealthy
        sys.exit(1)

    # report healthy
    sys.exit(0)


def main():
    sut = platform.node()
    # mqtt setup
    mqtt_broker = '10.245.128.14'
    status_topic = '%s/agent' % sut
    keepalive = 25  # seconds

    subscribe.callback(check_status,
                       status_topic,
                       qos=0,
                       userdata=None,
                       hostname=mqtt_broker,
                       keepalive=keepalive)


if __name__ == '__main__':
    main()
