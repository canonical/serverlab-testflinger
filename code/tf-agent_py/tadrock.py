#!/usr/bin/python3

import subprocess
import path

SUT = 'tadrock'

sut_path = path.join('data', 'testflinger-agent', 'sut', SUT)
log_path = path.join('data', 'testflinger-agent', 'agent_logs', SUT)

with open(log_path, 'w') as _file:
    agent = subprocess.Popen(
        ['testflinger-agent', '-c', (sut_path + '.conf')],
        stdout=_file,
        stderr=subprocess.STDOUT,
        check=True,
        text=True)
