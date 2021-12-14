#!/usr/bin/python3

"""Load specified SUT agents."""
# TODO:
# integrate w/ k8s & use http healthcheck?
# integrate smokeping (ping in/out), recieve from subproc?
# create fn to recieve health check in new thread?
# use thread timer for heartbeat send
# log heartbeat to dict/list and plot w/ elastics


from logging.handlers import RotatingFileHandler
from os import setgid, setuid, path, listdir
import subprocess
import threading
import argparse
import logging
import shlex
import time
import sys
import re
import psutil
import setproctitle
# from pudb import set_trace


def log_agent(pipe, sut, log_path, log_level):
    """Read stdout pipe."""
    def config_logging():
        logger = logging.getLogger(sut)
        # stdout output in debug mode
        stream_formatter = logging.Formatter(
            '>> %(name)s << \n   %(message)s')
        file_formatter = logging.Formatter(
            '%(message)s')
        # init logging handlers
        _stream_handler = logging.StreamHandler(sys.stdout)
        _file_handler = RotatingFileHandler(
            log_path,
            mode='a',
            backupCount=2,
            maxBytes=100000000)  # 100mb
        # set logging levels
        _stream_handler.setLevel(log_level)
        _file_handler.setLevel(logging.INFO)
        # assign formatters
        _stream_handler.setFormatter(stream_formatter)
        _file_handler.setFormatter(file_formatter)
        # add handlers to logger
        logger.addHandler(_stream_handler)
        logger.addHandler(_file_handler)

        return logger

    start_time = time.time()
    logger = config_logging()
    # break semaphore
    # sigint = {'stop': False}

    # wait for root log handlers to clear
    time.sleep(3)

    while True:
        cur_dur = time.time() - start_time
        line = pipe.readline().rstrip('\n')
        logger.info('|+%.1fs|\n%s' % (cur_dur, line))

        # try:
        #     logger.debug(pipe.readline())
        # # except KeyboardInterrupt:
        #     break
        #     sigint['stop'] = True

    # return sigint


def delegate(user_uid, user_gid, sut):
    """Execute as different user."""
    def preempt():
        setgid(user_gid)
        setuid(user_uid)
    return preempt


def load_sut_agent(sut_conf, work_dir, conf_dir, log_dir, log_level):
    """Load specified SUT agent."""
    conf_path = path.join(conf_dir, sut_conf)
    sut = path.splitext(sut_conf)[0]
    _log_path = path.join(log_dir, sut)
    # daemonize agent
    cmd = shlex.split(
        'setsid testflinger-agent -c %s' % conf_path)

    try:
        proc = subprocess.Popen(  # pylint: disable=w1509
            cmd,
            preexec_fn=delegate(1000, 1000, sut),  # run as
            start_new_session=True,  # fork
            universal_newlines=True,
            encoding='utf-8',
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
    else:
        proc_thread = threading.Thread(target=log_agent,
                                       args=(proc.stdout,
                                             sut,
                                             _log_path,
                                             log_level))
        proc_thread.start()

        return sut

        # sigint = proc_thread.start()

        # if sigint:
        #     proc_thread.join()


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
                        dest='reset',
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

    # setup root (main) logger
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

    if user_args.reset or user_args.stop:
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
    # set_trace()

    for idx, sut_conf in enumerate(conf_list):
        sut = load_sut_agent(sut_conf,
                             work_dir,
                             conf_dir,
                             log_dir,
                             log_level)
        root_logger.debug('  * %s', sut)

        if idx == (len(conf_list) - 1):  # last sut
            # stop root logging handlers
            root_logger.handlers.clear()
            print('=====================\n')


if __name__ == '__main__':
    main()
