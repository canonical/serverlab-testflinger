#!/usr/bin/python3

import paho.mqtt.subscribe as subscribe
import platform
import sys
# user agent checks


# def check_status(client, userdata, message):
def check_status(message):
    if 'online' or 'ok' in message:
        # report healthy
        # print(message)
        sys.exit(0)

    # report unhealthy
    # print(message)
    sys.exit(1)


def main():
    sut = platform.node()
    # mqtt setup
    mqtt_broker = '10.245.128.14'
    status_topic = '%s/agent' % sut
    keepalive = 25  # seconds

    # subscribe.callback(check_status,
    #                    status_topic,
    #                    qos=1,
    #                    userdata=None,
    #                    hostname=mqtt_broker,
    #                    keepalive=keepalive)

    message = subscribe.simple(status_topic,
                               hostname=mqtt_broker,
                               retained=False,
                               keepalive=keepalive)
    check_status(message.payload).decode('UTF-8')


if __name__ == '__main__':
    main()
