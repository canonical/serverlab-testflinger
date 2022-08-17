#!/usr/bin/python3

import paho.mqtt.subscribe as subscribe
import platform
import sys
# from pudb import set_trace; set_trace()


def check_status(message, agnt_cond, outpt_cond, ok):
    if any(cond in message for cond in agnt_cond):
        ok = True

    if any(cond in message for cond in outpt_cond):
        ok = False

    return ok


def main():
    sut = platform.node()
    # mqtt setup
    mqtt_broker = '10.245.128.14'
    agnt_topic = '%s/agent' % sut
    outpt_topic = '%s/output' % sut
    keepalive = 25  # seconds

    # define healthcheck triggers
    # (positive) conditions for agent topic
    agnt_cond = ('online', 'ok')
    # (negative) conditions for output topic
    outpt_cond = ('TESTFLINGER-DEVICE-OFFLINE',)

    agnt_msg = subscribe.simple(agnt_topic,
                                hostname=mqtt_broker,
                                retained=False,
                                keepalive=keepalive)

    outpt_msg = subscribe.simple(outpt_topic,
                                 hostname=mqtt_broker,
                                 retained=False,
                                 keepalive=keepalive)

    messages = (agnt_msg, outpt_msg)
    ok = False

    for message in messages:
        ok = check_status(
            (message.payload).decode('UTF-8'), agnt_cond, outpt_cond, ok)

    if ok:
        # report healthy
        sys.exit(0)

    # report unhealthy
    sys.exit(1)


if __name__ == '__main__':
    main()
