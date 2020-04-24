#!/usr/bin/python

# Helper script to auto-run a command when files are modified.

import os
import subprocess
import sys
import time

def run(cmd):
    now = time.asctime()
    print('[{}] : running {}'.format(now, cmd))
    return subprocess.check_output(cmd)

watchpath = sys.argv[1]
print('watchpath:', watchpath)
times = {}

while True:
    for path, _, files in os.walk(watchpath):
        for name in files:
            cmd = []
            base, ext = os.path.splitext(name)
            filename = os.path.join(path, name)
            mtime = os.path.getmtime(filename)
            if times.get(filename) != mtime:
                if ext == '.itl':
                    cmd = ['python', os.path.join('src', 'adapter.py'), filename]
            times[filename] = mtime
            if cmd:
                try:
                    print(run(cmd))
                except Exception as e:
                    print('failed:', e)
    sys.stdout.flush()
    time.sleep(0.25)
