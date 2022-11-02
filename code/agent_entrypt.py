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

from logging.handlers import RotatingFileHandler
from threading import Thread, Timer, Event
from pathlib import PurePath, Path
import paho.mqtt.client as mqtt
import subprocess
import platform
import requests
import logging
import signal
import shlex
import time
import sys
import re
# from pudb import set_trace


class LoopTimer(Timer):
    """Repeat thread timer."""

    def run(self):
        # insert loop
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class LogAgent(Thread):
    """Read stdout pipe."""

    def __init__(self, pipe, sut, log_path, exit_event):
        Thread.__init__(self)
        # thread ops
        self.daemon = True
        self.status_timer = None
        self.req_timer = None
        self.exit_event = exit_event
        # logging ops
        self.pipe = pipe
        self.sut = sut
        self.log_path = log_path
        # c3 setup
        self.c3_timeout = 300  # seconds
        self.c3_url = (
            'https://certification.canonical.com/submissions')
        # mqtt setup
        self.mqtt_broker = '10.245.128.14'
        self.status_topic = '%s/agent' % sut
        self.c3_topic = '%s/c3' % sut
        self.output_topic = '%s/output' % sut
        self.submit_topic = '%s/last_job' % sut
        self.mqtt_client = mqtt.Client(sut)
        # init logging
        self.config_pipe_logging()
        # setup mqtt
        self.init_mqtt()
        # init aux ops
        self.start_aux_threads()
        # start logging
        self.parse_pipe()

    def config_pipe_logging(self):
        """Configure loggers."""
        def overwrite_rotator(*args):
            # ignore dest log file
            log_f = args[0]
            # zero out log file
            with open(log_f, 'w') as file:
                file.seek(0)
                file.truncate()

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(message)s')
        file_handler = RotatingFileHandler(
            self.log_path,
            backupCount=1,
            maxBytes=300000000)  # 300mb
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        # use custom file rotator
        file_handler.rotator = overwrite_rotator
        # setup base logger
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        # add handlers for stream, file
        logger.addHandler(stdout_handler)
        logger.addHandler(file_handler)
        # disable verbose requests logging
        logging.getLogger('requests').setLevel(logging.CRITICAL)

    def init_mqtt(self):
        """Setup and connect MQTT."""
        def on_connect(*args):
            del args  # args unused
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
        # related to healthchk intvl
        status_interval = 20.0  # seconds
        self.status_timer = LoopTimer(status_interval,
                                      self.publish_status)
        self.status_timer.daemon = True

        # c3 request thread
        req_interval = 600.0  # seconds
        self.req_timer = LoopTimer(req_interval,
                                   self.request_c3)
        self.req_timer.daemon = True

        self.req_timer.start()
        self.status_timer.start()

    def cleanup_tasks(self):
        self.status_timer.cancel()
        self.req_timer.cancel()
        # close mqtt client
        self.mqtt_client.loop_stop()

    def publish_status(self):
        """Agent status thread."""
        # add logic, conditions
        message = 'ok'

        try:
            self.mqtt_client.publish(self.status_topic,
                                     payload=message)
        except Exception:  # soft failure
            pass

    def request_c3(self):
        """Non-blocking HTTP call."""
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

        message = 'state: %s | resp_t: %.2f sec' % (status[0],
                                                    status[1])
        logging.debug('[ C3 %s ]', message)

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
            logging.info(line)

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

            if self.exit_event.is_set():
                break

        self.cleanup_tasks()


def load_sut_agent(conf_path, log_dir):
    """Load specified SUT agent."""
    def handle_exit(*args):
        del args  # args unused
        print('\n\n[ terminating agent ]')
        exit_event.set()

        try:
            proc.terminate()
        finally:
            proc.kill()

    def define_signals():
        # provide process cleanup on terminate
        signal.signal(signal.SIGTERM, handle_exit)
        signal.signal(signal.SIGQUIT, handle_exit)
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGHUP, handle_exit)

    sut = PurePath(conf_path).stem
    log_path = Path(
        log_dir, sut).with_suffix('.log')
    # use string for shell=True
    # cmd = 'exec testflinger-agent -c %s' % conf_path
    cmd = shlex.split(
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
        print('# unable to start %s agent!' % sut)
    else:
        exit_event = Event()
        define_signals()

        log_thread = Thread(target=LogAgent,
                            args=(proc.stdout,
                                  sut,
                                  log_path,
                                  exit_event))
        log_thread.start()

        return sut


def main():
    """Load specified SUT agents."""
    # config dir of sut confs
    conf_dir = Path('/', 'data', 'testflinger-agent', 'sut')
    log_dir = PurePath('/', 'var', 'log')
    hostname = platform.node()
    conf_path = PurePath(
        conf_dir, hostname).with_suffix('.conf')

    for file in conf_dir.iterdir():
        if file == conf_path:
            load_sut_agent(conf_path, log_dir)
            break
    else:
        print('# agent conf file not found!')


if __name__ == '__main__':
    main()
