#!/usr/bin/python3

from os import path, listdir, setgid, setuid, setsid
import subprocess
import shlex
# from pudb import set_trace; set_trace()

work_dir = path.join('/', 'data', 'testflinger-agent')
conf_dir = path.join(work_dir, 'sut')
log_dir = path.join('/', 'var', 'log', 'sut-agent')

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Starting SUT agent(s):')


def delegate(user_uid, user_gid):
    "Execute as different user."
    def preempt():
        # daemonize
        setsid()
        # chuser
        setgid(user_gid)
        setuid(user_uid)
    return preempt


for sut_conf in listdir(conf_dir):
    sut = path.splitext(sut_conf)[0]
    log_path = path.join(log_dir, sut)
    conf_path = path.join(conf_dir, sut_conf)
    # easier to read
    cmd = shlex.split(
        'testflinger-agent -c %s' % conf_path)

    try:
        with open(log_path, 'w') as _file:
            agent = subprocess.Popen(
                cmd,
                preexec_fn=delegate(1000, 1000),  # run as ubuntu
                shell=False,
                start_new_session=True,
                cwd=work_dir,
                universal_newlines=True,
                encoding='utf-8',
                stdout=_file,
                stderr=subprocess.STDOUT)
    except OSError:
        print('  - Unable to start agent for: %s' % sut)
        continue
    else:
        print('  * %s' % sut)


# add argparse so you can call and load a specific sut or list
# of suts. the default arg would be to iterate over entire dir
# (or create seperate reload tool)
# for day-to-day ops