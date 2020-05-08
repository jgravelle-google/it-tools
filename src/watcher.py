#!/usr/bin/python

# Helper script to auto-run a command when files are modified.

import os
import subprocess
import sys
import time
import traceback

def run(cmd):
    now = time.asctime()
    print('[{}] : running {}'.format(now, cmd))
    pid = subprocess.Popen(cmd)
    return pid.communicate()

watchpath = sys.argv[1]
assert(sys.argv[2] == '--')
cmd = sys.argv[3:]
print 'watchpath:', watchpath
print 'command:', cmd

times = {}
def update_times():
    updated = False
    for path, _, files in os.walk(watchpath):
        for name in files:
            base, ext = os.path.splitext(name)
            filename = os.path.join(path, name)
            mtime = os.path.getmtime(filename)
            if times.get(filename) != mtime:
                updated = True
            times[filename] = mtime
    return updated
while True:
    if update_times():
        try:
            print ''
            sys.stdout.flush()
            run(cmd)
        except Exception as e:
            trace = traceback.format_exc(e)
            print trace
        # re-cache times for any build artifacts
        update_times()
    sys.stdout.flush()
    time.sleep(0.25)
