#!/usr/bin/python3

"""Load specified SUT agents."""

from os import setgid, setuid, path, listdir
import subprocess
import threading
import argparse
import logging
import shlex
import sys
# from pudb import set_trace; set_trace()


def read_output(pipe, sut, log_path, log_level):
    """Read stdout pipe."""
    def config_logging():
        # init named logger
        logger = logging.getLogger(sut)
        # stdout output in debug mode
        stream_formatter = logging.Formatter(
            '>> %(name)s << \n   %(message)s')
        file_formatter = logging.Formatter('%(message)s')
        # init logging handlers
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(log_path, mode='w')
        # set logging levels
        stream_handler.setLevel(log_level)
        file_handler.setLevel(logging.DEBUG)
        # assign formatters
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)
        # add handlers to logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        return logger

    logger = config_logging()
    # break semaphore
    # sigint = {'stop': False}

    while True:
        logger.debug(pipe.readline())
        # try:
        #     logger.debug(pipe.readline())
        # # except KeyboardInterrupt:
        #     break
        #     sigint['stop'] = True

    # return sigint


def delegate(user_uid, user_gid):
    """Execute as different user."""
    def preempt():
        setgid(user_gid)
        setuid(user_uid)

    return preempt


def load_sut_agent(sut_conf, work_dir, conf_dir, log_dir, log_level):
    """Load specified SUT agent."""
    sut = path.splitext(sut_conf)[0]
    log_path = path.join(log_dir, sut)
    conf_path = path.join(conf_dir, sut_conf)
    # daemonize agent
    cmd = shlex.split(
        'setsid testflinger-agent -c %s' % conf_path)

    try:
        proc = subprocess.Popen(  # pylint: disable=w1509
            cmd,
            preexec_fn=delegate(1000, 1000),  # run as
            start_new_session=True,  # fork
            universal_newlines=True,
            encoding='utf-8',
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
    else:
        print('  * %s' % sut)
        proc_thread = threading.Thread(target=read_output,
                                       args=(proc.stdout,
                                             sut,
                                             log_path,
                                             log_level))
        proc_thread.start()
        # sigint = proc_thread.start()

        # if sigint:
        #     proc_thread.join()


def parse_args():
    """Ingest arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '-D', '--debug',
                        dest='log_level',
                        action='store_const',
                        const=logging.DEBUG,
                        # default logging level
                        default=logging.INFO,
                        help='debug/verbose output')
    args = parser.parse_args()

    return args


def main():
    """Load specified SUT agents."""
    # base dir of tf-agent
    work_dir = path.join('/', 'data', 'testflinger-agent')
    # config dir of sut confs
    conf_dir = path.join(work_dir, 'sut')
    # logging config
    log_dir = path.join('/', 'var', 'log', 'sut-agent')
    log_level = parse_args().log_level

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('Starting SUT agent(s):')

    # setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)

    for sut_conf in listdir(conf_dir):
        load_sut_agent(sut_conf, work_dir, conf_dir, log_dir, log_level)


if __name__ == '__main__':
    main()
