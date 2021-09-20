#!/usr/bin/python3

"Load specified SUT agents."

from os import path, listdir, setgid, setuid
import subprocess
import shlex


def delegate(user_uid, user_gid):
    "Execute as different user."
    def preempt():
        setgid(user_gid)
        setuid(user_uid)
    return preempt


def load_sut_agent(sut_conf, work_dir, conf_dir, log_dir):
    "Load specified SUT agent."
    sut = path.splitext(sut_conf)[0]
    log_path = path.join(log_dir, sut)
    conf_path = path.join(conf_dir, sut_conf)
    # daemonize
    cmd = shlex.split(
        'setsid testflinger-agent -c %s' % conf_path)

    try:
        with open(log_path, 'w') as _file:
            _ = subprocess.Popen(  # pylint: disable=w1509
                cmd,
                preexec_fn=delegate(1000, 1000),  # run as
                start_new_session=True,
                universal_newlines=True,
                encoding='utf-8',
                cwd=work_dir,
                stdout=_file,
                stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
    else:
        print('  * %s' % sut)


def main():
    "Load specified SUT agents."
    work_dir = path.join('/', 'data', 'testflinger-agent')
    conf_dir = path.join(work_dir, 'sut')
    log_dir = path.join('/', 'var', 'log', 'sut-agent')

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('Starting SUT agent(s):')

    for sut_conf in listdir(conf_dir):
        load_sut_agent(sut_conf, work_dir, conf_dir, log_dir)


if __name__ == '__main__':
    main()
