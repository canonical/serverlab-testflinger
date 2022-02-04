#!/usr/bin/python3

"""Load specified SUT agents."""
# TODO:
# integrate w/ k8s & use http healthcheck?
# integrate smokeping (ping in/out), recieve from subproc?
# create fn to recieve health check in new thread?
# use thread timer for heartbeat send (in progress)
# log heartbeat to dict/list and plot?
# filter sleep messages?
# add external api hook to restart a specific agent
#   create method/fn to facilitate
#   to prevent excessive master processes from spawning

from logging.handlers import RotatingFileHandler
from os import setgid, setuid, path, listdir
from threading import Thread, Timer
import paho.mqtt.client as mqtt
import subprocess
import requests
import argparse
import logging
import shlex
import time
import sys
import re
import psutil
import setproctitle
# from pudb import set_trace; set_trace()


class LoopTimer(Timer):
    """Repeat thread timer"""
    def run(self):
        # insert loop
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class LogAgent(Thread):
    """Read stdout pipe."""
    def __init__(self, pipe, sut, log_path, log_level):
        Thread.__init__(self)
        self.pipe = pipe
        self.sut = sut
        self.log_path = log_path
        self.log_level = log_level
        self.pipe_logger = self.config_pipe_logging()
        # max c3 reply time
        self.c3_timeout = 2  # seconds
        self.c3_url = (
            'https://certification.canonical.com/submissions')
        # mqtt start
        self.client = mqtt.Client(sut)
        self.client.connect('10.245.128.14')
        # wait for root loggers to clear
        time.sleep(3)
        self.start_aux_threads()
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
        stream_handler.setLevel(self.log_level)
        file_handler.setLevel(logging.DEBUG)
        # assign formatters
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)

        # add handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        return logger

    def start_aux_threads(self):
        # mqtt status thread
        def_topic = '%s/logger' % (self.sut)
        def_message = 'ok'
        mqtt_interval = 120.0  # seconds
        mqtt_timer = LoopTimer(mqtt_interval,
                               self.publish_message,
                               [def_topic, def_message])
        mqtt_timer.daemon = True

        # c3 request thread
        req_interval = 120.0  # seconds
        req_timer = LoopTimer(req_interval,
                              self.request_c3)
        req_timer.daemon = True

        req_timer.start()
        mqtt_timer.start()

    def publish_message(self, topic, message):
        self.client.publish(topic, payload=message)

        # m_packet = self.client.publish(topic, payload=message)
        # m_packet.publish()

    def request_c3(self):
        """Non-blocking HTTP calls."""
        try:
            request = requests.get(
                self.c3_url, timeout=self.c3_timeout)
        except requests.Timeout:
            status = ('timeout', self.c3_timeout)
        else:
            if request.ok:
                status = ('ok', request.elapsed.total_seconds())
            else:
                status = ('error', 0.0)

        topic = ('%s/c3' % self.sut)
        message = '  [ C3 status: %s | resp_t: %.2f sec ]' % (status[0],
                                                              status[1])
        self.pipe_logger.debug(message)
        try:
            self.publish_message(topic, message)
        except Exception:
            pass

    def read_pipe(self):
        """Memory management."""
        while True:
            line = self.pipe.readline().rstrip('\n')
            yield line

    def parse_pipe(self):
        """Parse subprocess pipe"""
        topic = ('%s/sp_pipe' % self.sut)

        for idx, line in enumerate(self.read_pipe()):
            self.pipe_logger.info(line)
            try:
                self.publish_message(topic, line)
            except Exception:
                pass


def load_sut_agent(sut_conf, work_dir, conf_dir, log_dir, log_level):
    """Load specified SUT agent."""
    def delegate(user_gid, user_uid):
        """Execute as different user."""
        def preempt():
            setgid(user_gid)
            setuid(user_uid)
        return preempt

        # setproctitle.setproctitle('%s_agnt' % sut)

    conf_path = path.join(conf_dir, sut_conf)
    sut = path.splitext(sut_conf)[0]
    _log_path = path.join(log_dir, sut)
    # daemonize agent
    cmd = shlex.split(
        'setsid testflinger-agent -c %s' % conf_path)
    exe_group = 1000  # executing group
    exe_user = 1000  # executing user

    try:
        proc = subprocess.Popen(  # pylint: disable=w1509
            cmd,
            preexec_fn=delegate(exe_group, exe_user),
            start_new_session=True,  # fork
            universal_newlines=True,
            encoding='utf-8',
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
    else:
        log_thread = Thread(target=LogAgent,
                            args=(proc.stdout,
                                  sut,
                                  _log_path,
                                  log_level))
        log_thread.start()

        return sut


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
    parser.add_argument('-d', '-D', '--debug',
                        dest='log_level',
                        action='store_const',
                        const=logging.INFO,
                        # default logging level
                        default=logging.WARNING,
                        help='debug/verbose output')
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
    work_dir = path.join('/', 'data', 'testflinger-agent')
    # config dir of sut confs
    conf_dir = path.join(work_dir, 'sut')
    conf_list = listdir(conf_dir)
    # logging config
    log_dir = path.join('/', 'var', 'log', 'sut-agent')
    log_level = user_args.log_level

    # set main process name
    setproctitle.setproctitle('agent_main')

    root_logger = config_root_logging(log_dir)

    if user_args.restart or user_args.stop:
        # kill running agents (ps pname truncated)
        agent_procs = re.compile('agent_main|testflinger-age')

        # cat procs and kill named procs
        for proc in psutil.process_iter(['name']):
            if agent_procs.match(proc.info['name']):
                proc.kill()

        if user_args.stop:
            sys.exit()

    print('\n=========================')
    print('Loading SUT Agent(s):')

    for idx, sut_conf in enumerate(conf_list):
        sut = load_sut_agent(sut_conf,
                             work_dir,
                             conf_dir,
                             log_dir,
                             log_level)
        root_logger.debug('  * %s', sut)

        if idx == (len(conf_list) - 1):  # last sut
            # stop root logging handlers
            print('=====================\n')
            root_logger.handlers.clear()


if __name__ == '__main__':
    main()
