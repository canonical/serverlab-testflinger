#!/usr/bin/python3

# Copyright (C) 2022 Canonical Ltd.
#
# Authors
#   Adrian Lane <adrian.lane@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Load specified SUT submission agents."""

from threading import Thread, Timer
from os import path, listdir
from ruamel.yaml import YAML
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt
import setproctitle
import subprocess
import argparse
import shlex
import re
import psutil
import logging
import sys
# from pudb import set_trace


class LoopTimer(Timer):
    """Repeat thread timer."""

    def run(self):
        # insert loop
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class SubmitAgent(Thread):
    """Read stdout pipe."""

    def __init__(self, sut_conf, conf_dir, work_dir):
        Thread.__init__(self)
        self.sut = path.splitext(sut_conf)[0]
        self.sut_conf = sut_conf
        self.conf_dir = conf_dir
        self.conf_path = path.join(conf_dir, sut_conf)
        self.work_dir = work_dir
        # testflinger api server
        self.api_server = '10.245.128.10'
        # testflinger deploy release
        self.release = 'focal'
        # mqtt setup
        self.mqtt_broker = '10.245.128.14'
        self.status_topic = "%s/submit_status" % self.sut
        self.submit_topic = "%s/submit" % self.sut
        self.mqtt_client = mqtt.Client('%s_submit' % self.sut)
        self.init_mqtt()
        self.start_aux_threads()
        self.subscribe_agent()

    def init_mqtt(self):
        """Setup and connect MQTT."""
        def on_connect(*args):
            self.mqtt_client.publish(self.status_topic,
                                     payload='online')

        # set last will and testament
        message = 'offline'
        self.mqtt_client.will_set(self.status_topic,
                                  payload=message,
                                  retain=True)

        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.connect(self.mqtt_broker)

    def start_aux_threads(self):
        """Aux threads."""
        # mqtt ops thread
        self.mqtt_client.loop_start()

        # mqtt status thread
        status_interval = 30.0  # seconds
        status_timer = LoopTimer(status_interval,
                                 self.publish_status)
        status_timer.daemon = True

        status_timer.start()

    def publish_status(self):
        """Logger status thread."""
        # add logic
        message = 'publish cmd to %s/submit' % self.sut

        self.mqtt_client.publish(self.status_topic,
                                 payload=message)

    def subscribe_agent(self):
        """MQTT subscribe on message."""
        # add on_message fn
        keepalive = 60  # seconds

        subscribe.callback(self.submit_test,
                           self.submit_topic,
                           qos=0,
                           userdata=None,
                           hostname=self.mqtt_broker,
                           keepalive=keepalive)

    def update_yaml(self, test_cmd):
        """Update sut yaml."""
        ref_file = '.reference.yaml'
        ref_path = path.join(self.conf_dir, ref_file)
        yaml = YAML()

        with open(ref_path, 'r') as stream:
            data = stream.read()
            code = yaml.load(data)

        code['job_queue'] = self.sut
        code['provision_data']['distro'] = self.release
        code['test_data']['test_cmds'] = test_cmd

        with open(self.conf_path, 'w') as file:
            # overwrite
            file.seek(0)
            yaml.dump(code, file)
            file.truncate()

    def submit_test(self, client, userdata, message):
        """Callback method."""
        test_cmd = (message.payload).decode('UTF-8')
        self.update_yaml(test_cmd)

        cmd = shlex.split('testflinger-cli \
                          --server http://%s:8000 \
                          submit %s' % (self.api_server,
                                        self.conf_path))

        try:
            _ = subprocess.Popen(cmd,
                                 universal_newlines=True,
                                 encoding='utf-8',
                                 cwd=self.work_dir)
        except OSError:
            print('  - Unable to start agent for: %s' % self.sut)


def config_root_logging(log_dir):
    """Setup root (main) logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_formatter = logging.Formatter(
        '%(message)s --- %(asctime)s', "[%H:%M:%S %a %b %d]")

    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(
        path.join(log_dir, 'init_agents'), mode='w')
    stream_handler.setFormatter(root_formatter)
    file_handler.setFormatter(root_formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    return root_logger


def get_args():
    """Ingest arguments"""
    parser = argparse.ArgumentParser()
    # add logic to restart thread?
    # thread.stop() + thread.start()
    # kill main for restart?
    parser.add_argument('-r', '-R', '--restart',
                        dest='restart',
                        action='store_true',
                        help='restart all agents')
    parser.add_argument('-s', '-S', '--stop',
                        dest='stop',
                        action='store_true',
                        help='stop all agents')
    args = parser.parse_args()

    return args


def main():
    """Load specified SUT agents."""
    user_args = get_args()
    # base dir of tf-agent
    work_dir = path.join('/', 'data', 'testflinger-cli')
    # config dir of sut confs
    conf_dir = path.join(work_dir, 'sut')
    conf_list = listdir(conf_dir)
    # logging config
    log_dir = path.join('/', 'var', 'log', 'submit-agent')

    # set main process name
    setproctitle.setproctitle('submit_main')

    root_logger = config_root_logging(log_dir)

    if user_args.restart or user_args.stop:
        # kill running agents (ps pname truncated)
        agent_procs = re.compile('submit_main|testflinger-cli')

        # cat procs and kill named procs
        for proc in psutil.process_iter(['name']):
            if agent_procs.match(proc.info['name']):
                proc.kill()

        if user_args.stop:
            sys.exit()

    print('\n=========================')
    print('Loading SUT Submit Agents:')

    for idx, sut_conf in enumerate(conf_list):
        submit_thread = Thread(target=SubmitAgent,
                               args=(sut_conf,
                                     conf_dir,
                                     work_dir))
        submit_thread.start()

        sut = path.splitext(sut_conf)[0]
        root_logger.debug('  * %s', sut)

        if idx == (len(conf_list) - 1):  # last sut
            print('=====================\n')


if __name__ == '__main__':
    main()
