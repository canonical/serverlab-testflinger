#!/usr/bin/python3

import paho.mqtt.subscribe as subscribe
import platform
import sys
# user agent checks


# def check_status(client, userdata, message):
def check_status(message):
    if 'online' or 'ok' in message:
        # report healthy
        sys.exit(0)

    # report unhealthy
    sys.exit(1)


def main():
    sut = platform.node()
    # mqtt setup
    mqtt_broker = '10.245.128.14'
    status_topic = '%s/agent' % sut
    keepalive = 25  # seconds

    message = subscribe.simple(status_topic,
                               hostname=mqtt_broker,
                               retained=False,
                               keepalive=keepalive)
    check_status(message.payload).decode('UTF-8')


if __name__ == '__main__':
    main()
