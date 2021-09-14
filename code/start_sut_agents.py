#!/usr/bin/python3

import os
import subprocess
import path

conf_dir = path.join('data', 'testflinger-agent', 'sut')
log_dir = path.join('var', 'log', 'tf-agent')

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Starting SUT agent(s):')

for sut_conf in os.listdir(conf_dir):
    sut = path.splitext(sut_conf)[0]
    log_path = path.join(log_dir + sut)
    conf_path = path.join(conf_dir + sut_conf)

    try:
        with open(log_path, 'w') as _file:
            agent = subprocess.Popen(
                ['testflinger-agent', '-c', conf_path],
                stdout=_file,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                start_new_session=True,
                shell=True)
    except OSError:
        print('Unable to start agent for: %s', sut)
        continue
    else:
        print('  * %s agent loaded', sut)


# add argparse so you can call and load a specific sut
# default arg would be to iterate over entire dir
# (or create seperate reload tool)
# for day-to-day ops
