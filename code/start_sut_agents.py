#!/usr/bin/python3

"Load specified SUT agents."

import os
import subprocess
import shlex


def delegate(user_uid, user_gid):
    "Execute as different user."
    def preempt():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return preempt


def load_sut_agent(sut_conf, work_dir, conf_dir, log_dir):
    "Load specified SUT agent."
    sut = os.path.splitext(sut_conf)[0]
    # modify perms for logging
    log_path = os.path.join(log_dir, sut)
    conf_path = os.path.join(conf_dir, sut_conf)
    # daemonize
    cmd = shlex.split(
        'setsid testflinger-agent -c %s' % conf_path)

    try:
        with open(os.open(
                log_path, os.O_CREAT | os.O_WRONLY, 0o666), 'w') as logf:
            # pylint: disable=w1509
            _ = subprocess.Popen(
                cmd,
                preexec_fn=delegate(1000, 1000),  # run as
                start_new_session=True,
                universal_newlines=True,
                encoding='utf-8',
                cwd=work_dir,
                stdout=logf,
                stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
    else:
        print('  * %s' % sut)


def main():
    "Load specified SUT agents."
    work_dir = os.path.join('/', 'data', 'testflinger-agent')
    conf_dir = os.path.join(work_dir, 'sut')
    log_dir = os.path.join('/', 'var', 'log', 'sut-agent')

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('Starting SUT agent(s):')

    for sut_conf in os.listdir(conf_dir):
        load_sut_agent(sut_conf, work_dir, conf_dir, log_dir)


if __name__ == '__main__':
    main()
