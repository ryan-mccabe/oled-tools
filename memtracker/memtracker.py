#!/usr/bin/python
#
# Copyright (c) 2021, Oracle and/or its affiliates. All rights reserved.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
#
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.
#
import os
import sys
import signal
import argparse
import time
import subprocess
from datetime import datetime

OUTFILE="/var/oled/memtracker"
LOGROTATEFILE="/etc/logrotate.d/memtracker"
VERSION=1.2
DEF_DELAY=5

# Files to log
FILES_TO_LOG = [
        "/proc/vmstat",
        "/proc/buddyinfo",
        "/proc/slabinfo",
        "/proc/pagetypeinfo",
        "/proc/zoneinfo",
        "/sys/kernel/debug/extfrag/extfrag_index",
        "/sys/kernel/debug/extfrag/unusable_index",
        "/sys/kernel/debug/extfrag/compactinfo",
        "/sys/kernel/debug/alloc_last_chance/stats",
        "/sys/kernel/slab/dentry/objects",
        "/sys/kernel/slab/dentry/objects_partial",
        "/sys/kernel/slab/dentry/total_objects"]

# Some procfs and sysfs files are expensive to read since they can add
# additional locking paths or load on the kernel. Avoid reading such
# files more often than every 10 minutes. FOllowing is a list of such files
EXPENSIVE_FILES=["pagetypeinfo|compactinfo"]
EXPENSIVE_DELAY=596

# Up to 5 commands to execute for each sampleing interval and log the
# results from
CMD1="numastat -m"
CMD2="uname -a"
CMD3=""
CMD4=""
CMD5=""


def cleanup(signum, frame):
    print("Interrupt! Cleaning up\n")
    os.remove(LOGROTATEFILE)
    sys.exit(0)

def setup_logrotate():
    f = open(LOGROTATEFILE,"w")
    f.write(OUTFILE + " {\n")
    f.write("\tcompress\n")
    f.write("\tcopytruncate\n")
    f.write("\tmissingok\n")
    f.write("\trotate 15\n")
    f.write("\tdaily\n")
    f.write("}\n")
    f.close()

def get_files(logf):
    global start_time
    timestamp = datetime.today()
    logf.write("======== zzz %s" % timestamp.strftime('%Y-%m-%d %H:%M:%S') + " ========\n")
    for fname in FILES_TO_LOG:
        # Check if file is readable
        if not os.access(fname, os.R_OK):
            continue

        # Check if it is one of the files expensive to read
        if fname in EXPENSIVE_FILES:
            end_time = time.time()
            if (end_time - start_time) < EXPENSIVE_DELAY:
                continue
            else:
                start_time = time.time()

        fd = open(fname, "r")
        logf.write("%s\n" % fname)
        data = fd.read()
        logf.write(data)
    logf.flush()

def run_cmd(cmdname, logf):
    if cmdname == "":
        return
    logf.write("==============================\n")
    logf.write("%s\n" % cmdname)
    try:
        output = subprocess.Popen(cmdname.split(' ', 1),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()[0]
        logf.write(output)
    except:
        return

# Check if we are running as root
if not os.geteuid()==0:
    sys.exit('You must be root to run this script.')


# Parse arguments
parser = argparse.ArgumentParser(description =
        "Log memory usage data continuously.")
parser.add_argument("interval", type=int, default=DEF_DELAY, nargs='?',
            help="delay in minutes between samples (default is 5)")
args = parser.parse_args()
print("Capturing memtracker data in file " + OUTFILE + " every " + str(args.interval) \
        + " minute(s); press Ctrl-c to exit.")


# Trap ctrl-c and other termination signals
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGHUP, cleanup)
signal.signal(signal.SIGQUIT, cleanup)


# Set up log file created by this script to be rotated by logrotate
setup_logrotate()


# Initialize a start time so expensive files will still be logged
# when this script starts running
start_time = time.time()
start_time = start_time - EXPENSIVE_DELAY - 1

# Open logfile and write out a header
outf = open(OUTFILE,"a+")
outf.write("\n")
outf.write("#######################################\n")
outf.write("# Memtracker version %d\n" % VERSION)
outf.write("#######################################\n")
outf.write("\n")
outf.flush()


# Now loop forever logging information every "interval" minutes
while True:
    get_files(outf)
    if CMD1 != "":
        run_cmd(CMD1, outf)
    if CMD2 != "":
        run_cmd(CMD2, outf)
    if CMD3 != "":
        run_cmd(CMD3, outf)
    if CMD4 != "":
        run_cmd(CMD4, outf)
    if CMD5 != "":
        run_cmd(CMD5, outf)
    outf.write("==============================\n")
    outf.flush()
    time.sleep(args.interval*60)

os.remove(LOGROTATEFILE)
