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

"""Load specified SUT agents."""

# Todo:
# restart agent via mqtt?

from logging.handlers import RotatingFileHandler
from threading import Thread, Timer
from pathlib import PurePath
from os import listdir, uname
import paho.mqtt.client as mqtt
import subprocess
import requests
import logging
import shelx
import time
import sys
import re
# from pudb import set_trace; set_trace()


class LoopTimer(Timer):
    """Repeat thread timer."""

    def run(self):
        # insert loop
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class LogAgent(Thread):
    """Read stdout pipe."""

    def __init__(self, pipe, sut, log_path):
        Thread.__init__(self)
        self.daemon = True
        self.pipe = pipe
        self.sut = sut
        self.log_path = log_path
        self.pipe_logger = self.config_pipe_logging()
        # max c3 reply time
        self.c3_timeout = 2  # seconds
        self.c3_url = (
            'https://certification.canonical.com/submissions')
        # mqtt setup
        self.mqtt_broker = '10.245.128.14'
        self.status_topic = '%s/agent' % sut
        self.c3_topic = '%s/c3' % sut
        self.output_topic = '%s/output' % sut
        self.submit_topic = '%s/last_job' % sut
        self.mqtt_client = mqtt.Client(sut)
        self.init_mqtt()
        # aux ops
        self.start_aux_threads()
        # wait for root loggers to clear
        time.sleep(3)
        self.parse_pipe()

    def config_pipe_logging(self):
        """Configure loggers."""
        logger = logging.getLogger(self.sut)
        # stdout output in debug mode
        stream_formatter = logging.Formatter(
            '>> %(name)s << \n   %(message)s')
        file_formatter = logging.Formatter(
            '%(message)s')

        # init logging handlers
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler = RotatingFileHandler(
            self.log_path,
            mode='a',
            backupCount=2,
            maxBytes=100000000)  # 100mb
        # set logging levels
        stream_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.DEBUG)
        # assign formatters
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)

        # add handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        return logger

    def init_mqtt(self):
        """Setup and connect MQTT."""
        def on_connect(*args):
            _message = 'online'
            for idx, _topic in enumerate(topics):
                if idx:
                    time.sleep(.3)
                    _message = '...'

                self.mqtt_client.publish(_topic,
                                         payload=_message)

        # non-retained topics
        topics = (self.status_topic, self.c3_topic)

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
        status_interval = 60.0  # seconds
        status_timer = LoopTimer(status_interval,
                                 self.publish_status)
        # terminate child thread on exit
        status_timer.daemon = True

        # c3 request thread
        req_interval = 60.0  # seconds
        req_timer = LoopTimer(req_interval,
                              self.request_c3)
        req_timer.daemon = True

        req_timer.start()
        status_timer.start()

    def publish_status(self):
        """Agent status thread."""
        # add logic, conditions
        message = 'ok'
        # (maybe) add timeout for last seen line
        # add ip addr publish

        try:
            self.mqtt_client.publish(self.status_topic,
                                     payload=message)
        except Exception:  # specify
            pass

    def request_c3(self):
        """Non-blocking HTTP calls."""
        try:
            request = requests.get(self.c3_url,
                                   timeout=self.c3_timeout)
        except requests.Timeout:
            status = ('timeout', self.c3_timeout)
        else:
            if request.ok:
                status = ('ok', request.elapsed.total_seconds())
            else:
                status = ('error', 0.0)

        message = 'status: %s | resp_t: %.2f sec' % (status[0],
                                                     status[1])
        self.pipe_logger.debug('  [ C3 %s ]', message)

        try:
            self.mqtt_client.publish(self.c3_topic,
                                     payload=message)
        except Exception:  # soft failure
            pass

    def read_pipe(self):
        """Memory management."""
        while True:
            line = self.pipe.readline().rstrip('\n')
            yield line

    def parse_pipe(self):
        """Parse subprocess pipe. """
        submit_line = re.compile('Starting\\sjob')

        for line in self.read_pipe():
            self.pipe_logger.info(line)

            # parse for mqtt
            job_match = submit_line.search(line)
            if job_match:
                # only publish job id, consume msg
                line = line[-36:]
                try:
                    self.mqtt_client.publish(self.submit_topic,
                                             payload=line,
                                             retain=True)
                except Exception:  # soft failure
                    pass
            else:
                try:
                    self.mqtt_client.publish(self.output_topic,
                                             payload=line,
                                             retain=True)
                except Exception:  # soft failure
                    pass


def load_sut_agent(sut_conf, conf_dir, log_dir):
    """Load specified SUT agent."""
    conf_path = PurePath(conf_dir, sut_conf)
    sut = PurePath(sut_conf).stem
    log_path = PurePath(
        log_dir, sut).with_suffix('.log')
    # use string for shell=True
    # cmd = 'testflinger-agent -c %s' % conf_path
    cmd = shelx.split(
        'testflinger-agent -c %s' % conf_path)

    try:
        proc = subprocess.Popen(
            cmd,
            # shell=True,  # testing
            # executable='/bin/bash',
            text=True,
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except OSError:
        print('  - unable to start %s agent!' % sut)
    else:
        log_thread = Thread(target=LogAgent,
                            args=(proc.stdout,
                                  sut,
                                  log_path))
        log_thread.start()

        return sut


def main():
    """Load specified SUT agents."""
    # config dir of sut confs
    conf_dir = PurePath('/', 'conf')
    conf_list = listdir(conf_dir)
    # logging config
    log_dir = PurePath('/', 'var', 'log')
    # move to cntnr name?
    hostname = uname().getnodename

    for sut_conf in conf_list:
        if (sut_conf.startswith(
                hostname) and sut_conf.endswith('.conf')):
            load_sut_agent(sut_conf,
                           conf_dir,
                           log_dir)


if __name__ == '__main__':
    main()
