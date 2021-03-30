#!/usr/bin/python -tt
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
import fcntl
from datetime import datetime

OUTFILE="/var/oled/memtracker/memtracker.log"
LOGROTATEFILE="/etc/logrotate.d/memtracker"
VERSION=1.2
DEF_DELAY=5
LOCK_FILE_DIR = "/run/lock/"
LOCK_FILE_DIR_OL6 = "/var/run/"

# Files to log
FILES_TO_LOG = [
        "/proc/meminfo",
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

# Up to 5 commands to execute for each sampling interval and log the
# results from
CMD1="numastat -m"
CMD2="uname -a"
CMD3=""
CMD4=""
CMD5=""

# Global variables
lock_fd = None
lock_filename = ""

def cleanup(signum, frame):
    global lock_fd
    global lock_filename
    print("Interrupt! Cleaning up\n")
    os.remove(LOGROTATEFILE)
    lock_fd.close()
    os.remove(lock_filename)
    sys.exit(0)

def setup_logrotate():
    f = open(LOGROTATEFILE,"w")
    f.write(OUTFILE + " {\n")
    f.write("\trotate 20\n")
    f.write("\tsize 20M\n")
    f.write("\tcopytruncate\n")
    f.write("\tcompress\n")
    f.write("\tmissingok\n")
    f.write("}\n")

    f.close()

def create_lock():
    """ Creates the directory and lock file """
    global lock_fd
    global lock_filename
    if os.path.exists(LOCK_FILE_DIR):
        parent_dir = os.path.join(LOCK_FILE_DIR, "memtracker")
    else:
        parent_dir = os.path.join(LOCK_FILE_DIR_OL6, "memtracker")
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, mode=0o700)
        except Exception as e:
            print("Could not create directory " + parent_dir + ": " + str(e))
            return

    lock_filename = os.path.join(parent_dir, "lock")
    lock_fd = open(lock_filename, "w")

    # Exclusive lock | non-blocking request
    op = fcntl.LOCK_EX | fcntl.LOCK_NB
    try:
        fcntl.flock(lock_fd, op)
    except IOError as e:
        print("Another instance of this script is running; please kill that instance " \
                "if you want to restart the script.")
        sys.exit(1)

def disk_space_available(path):
    cmd = "df -Ph " + path
    try:
        output = subprocess.Popen(cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()[0].decode('utf-8')
    except:
        print("Unable to compute disk utilization for " + path + ".")
        return False
    line = ""
    for line in output.splitlines():
        if "Use" in line:
            pos_use = line.split().index("Use%")
            pos_avail = line.split().index("Avail")
            continue
    if not line:
        print("Unable to compute disk utilization for " + path + ".")
        return False
    util = line.split()[pos_use][:-1]
    avail = line.split()[pos_avail][:-1]
    avail_unit = line.split()[pos_avail][-1]
    avail_space_mb = 0
    if avail_unit == "T":
        avail_space_mb = round(int(avail) * 1024 * 1024)
    elif avail_unit == "G":
        avail_space_mb = round(int(avail) * 1024)
    elif avail_unit == "M":
        avail_space_mb = int(avail)
    elif avail_unit == "K":
        avail_space_mb = round(int(avail) / 1024)

    print("Disk utilization of the partition for " + path + " is " + util \
            + "%; available space is " + str(avail_space_mb) + " MB.")

    # If disk space utilization is >= 85% OR if available space is less than 50 MB,
    # then error out. We do not want to fill up the filesystem with memtracker logs.
    if int(util) >= 85 or avail_space_mb < 50:
        return False
    return True


def get_files(logf):
    global start_time
    timestamp = datetime.now().strftime("<%m/%d/%Y %H:%M:%S>")
    logf.write("======== zzz %s" % timestamp + " ========\n")
    for fname in FILES_TO_LOG:
        # Check if file is readable
        if not os.access(fname, os.R_OK):
            continue

        # Check if it is one of the files expensive to read
        if fname in EXPENSIVE_FILES:
            end_time = time.time()
            if (end_time - start_time) < EXPENSIVE_DELAY:
                continue
            start_time = time.time()

        fd = open(fname, "r")
        if not fd:
            continue
        logf.write("%s:\n" % fname)
        data = fd.read()
        logf.write(data)
        logf.write("==============================\n")
    logf.flush()

def run_cmd(cmdname, logf):
    if cmdname == "":
        return
    logf.write("%s:\n" % cmdname)
    try:
        output = subprocess.Popen(cmdname.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()[0].decode('utf-8')
        logf.write(output)
        logf.write("==============================\n")
    except:
        return


def rotate_logfile():
    os.system("logrotate " + LOGROTATEFILE)


# Check if we are running as root
if not os.geteuid()==0:
    sys.exit('You must be root to run this script.')


# Parse arguments
parser = argparse.ArgumentParser(description =
        "Log memory usage data continuously.")
parser.add_argument("interval", type=int, default=DEF_DELAY, nargs='?',
            help="delay in minutes between samples (default is 5)")
args = parser.parse_args()
if args.interval < 1:
    print("Invalid interval argument.")
    parser.print_help()
    sys.exit(1)


# Create a lock file so as to prevent multiple instances of this script from running
create_lock()


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


# Open logfile
end = OUTFILE.rfind("/")
parent_dir = OUTFILE[0:end]
if not os.path.exists(parent_dir):
    try:
        os.makedirs(parent_dir)
    except IOError as e:
        print("Could not create directory " + parent_dir + ": " + str(e))
        sys.exit(1)

# Check if there's enough space available on disk
if not disk_space_available(parent_dir):
    print("Exiting! There is not enough disk space available in " \
            + str(parent_dir) + "; check the man page for more details.")
    sys.exit(1)

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
    rotate_logfile()
