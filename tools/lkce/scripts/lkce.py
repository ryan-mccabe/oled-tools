#!/usr/bin/env python3
#
# Copyright (c) 2023, Oracle and/or its affiliates.
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
# program for user-interaction
#
import fcntl
import glob
import os
import platform
import re
import shutil
import stat
import subprocess  # nosec
import sys
from typing import Mapping, Optional


def update_key_values_file(
        path: str,
        key_values: Mapping[str, Optional[str]],
        sep: str) -> None:
    """Update key-values in a file.

    For all (key, new_value) pairs in key_values, if value is not None, update
    the value of that key in the file to new_value; otherwise remove the
    key-value pair from the file.  The file is assumed to have a key-value per
    line, with sep as separator.  A line might contain only a key, even without
    a separator, in which case the value is assumed to be empty.
    """
    with open(path) as fdesc:
        data = fdesc.read().splitlines()

    with open(path, "w") as fdesc:
        for line in data:
            key, *_ = line.split("=", maxsplit=1)
            key = key.strip()

            if key in key_values:
                new_value = key_values[key]

                # If new_value is not None, update the value; otherwise remove
                # it (i.e. don't write key-new_value back to the file).
                if new_value is not None:
                    fdesc.write(f"{key}{sep}{new_value}\n")
            else:
                # line doesn't match lines to update; write it back as is
                fdesc.write(f"{line}\n")


class Lkce:
    def __init__(self):
        # global variables
        self.LKCE_HOME = "/etc/oled/lkce"
        self.LKCE_CONFIG_FILE = self.LKCE_HOME + "/lkce.conf"
        self.LKCE_OUTDIR = "/var/oled/lkce"
        self.LKCE_BINDIR = "/usr/lib/oled-tools"

        # vmlinux_path
        self.KDUMP_KERNELVER = platform.uname().release

        # default values
        self.ENABLE_KEXEC = "no"
        self.VMLINUX_PATH = "/usr/lib/debug/lib/modules/" + \
            self.KDUMP_KERNELVER + "/vmlinux"
        self.CRASH_CMDS_FILE = self.LKCE_HOME + "/crash_cmds_file"
        self.VMCORE = "yes"
        self.MAX_OUT_FILES = "50"

        # effective values
        self.enable_kexec = self.ENABLE_KEXEC
        self.vmlinux_path = self.VMLINUX_PATH
        self.crash_cmds_file = self.CRASH_CMDS_FILE
        self.vmcore = self.VMCORE
        self.lkce_outdir = self.LKCE_OUTDIR
        self.max_out_files = self.MAX_OUT_FILES

        # set values from config file
        if os.path.exists(self.LKCE_CONFIG_FILE):
            self.read_config(self.LKCE_CONFIG_FILE)

        # lkce as a kdump_pre hook to kexec-tools
        self.LKCE_KDUMP_SH = self.LKCE_HOME + "/lkce_kdump.sh"
        self.LKCE_KDUMP_DIR = self.LKCE_HOME + "/lkce_kdump.d"
        self.FSTAB = "/etc/fstab"
        self.KDUMP_CONF = "/etc/kdump.conf"
        self.TIMEOUT_PATH = shutil.which("timeout")
    # def __init__

    def configure_default(self):
        os.makedirs(self.LKCE_HOME, exist_ok=True)

        if self.enable_kexec == "yes":
            print("trying to disable lkce")
            self.disable_lkce_kexec()

        # crash_cmds_file
        filename = self.CRASH_CMDS_FILE
        content = """#
# This is the input file for crash utility. You can edit this manually
# Add your own list of crash commands one per line.
#
bt
bt -a
bt -FF
dev
kmem -s
foreach bt
log
mod
mount
net
ps -m
ps -S
runq
quit
"""
        file = open(filename, "w")
        file.write(content)
        file.close()

        # config file
        filename = self.LKCE_CONFIG_FILE
        content = """##
# This is configuration file for lkce
# Use 'oled lkce configure' command to change values
##

#enable lkce in kexec kernel
enable_kexec=""" + self.ENABLE_KEXEC + """

#debuginfo vmlinux path. Need to install debuginfo kernel to get it
vmlinux_path=""" + self.VMLINUX_PATH + """

#path to file containing crash commands to execute
crash_cmds_file=""" + self.CRASH_CMDS_FILE + """

#lkce output directory path
lkce_outdir=""" + self.LKCE_OUTDIR + """

#enable vmcore generation post kdump_report
vmcore=""" + self.VMCORE + """

#maximum number of outputfiles to retain. Older file gets deleted
max_out_files=""" + self.MAX_OUT_FILES

        file = open(filename, "w")
        file.write(content)
        file.close()

        print("configured with default values")
    # def configure_default

    def read_config(self, filename):
        if not os.path.exists(filename):
            return

        file = open(filename, "r")
        for line in file.readlines():
            if re.search("^#", line):  # ignore lines starting with '#'
                continue

            # trim space/tab/newline from the line
            line = re.sub(r"\s+", "", line)

            entry = re.split("=", line)
            if "enable_kexec" in entry[0] and entry[1]:
                self.enable_kexec = entry[1]

            elif "vmlinux_path" in entry[0] and entry[1]:
                self.vmlinux_path = entry[1]

            elif "crash_cmds_file" in entry[0] and entry[1]:
                self.crash_cmds_file = entry[1]

            elif "lkce_outdir" in entry[0] and entry[1]:
                self.lkce_outdir = entry[1]

            elif "vmcore" in entry[0] and entry[1]:
                self.vmcore = entry[1]

            elif "max_out_files" in entry[0] and entry[1]:
                self.max_out_files = entry[1]
    # def read_config

    def create_lkce_kdump(self):
        filename = self.LKCE_KDUMP_SH
        os.makedirs(self.LKCE_KDUMP_DIR, exist_ok=True)

        mount_cmd = "mount -o bind /sysroot"  # OL7 and above

        # create lkce_kdump.sh script
        content = """#!/bin/sh
# This is a kdump_pre script
# /etc/kdump.conf is used to configure kdump_pre script

# Generate vmcore post lkce_kdump scripts execution
LKCE_VMCORE=""" + self.vmcore + """

# Timeout for lkce_kdump scripts in seconds
LKCE_TIMEOUT="120"

# Temporary directory to mount the actual root partition
LKCE_DIR="/lkce_kdump"

mkdir $LKCE_DIR
""" + mount_cmd + """ $LKCE_DIR
mount -o bind /proc $LKCE_DIR/proc
mount -o bind /dev $LKCE_DIR/dev

LKCE_KDUMP_SCRIPTS=$LKCE_DIR""" + self.LKCE_KDUMP_DIR + """/*

#get back control after $LKCE_TIMEOUT to proceed
export LKCE_KDUMP_SCRIPTS
export LKCE_DIR
""" + self.TIMEOUT_PATH + """ $LKCE_TIMEOUT /bin/sh -c '
echo "LKCE_KDUMP_SCRIPTS=$LKCE_KDUMP_SCRIPTS";
for file in $LKCE_KDUMP_SCRIPTS;
do
	cmd=${file#$LKCE_DIR};
	echo "Executing $cmd";
	chroot $LKCE_DIR $cmd;
done;'

umount $LKCE_DIR/dev
umount $LKCE_DIR/proc
umount $LKCE_DIR

unset LKCE_KDUMP_SCRIPTS
unset LKCE_DIR

if [ "$LKCE_VMCORE" == "no" ]; then
	echo "lkce_kdump.sh: vmcore generation is disabled"
	exit 1
fi

exit 0
"""
        file = open(filename, "w")
        file.write(content)
        file.close()

        mode = os.stat(filename).st_mode
        os.chmod(filename, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # def create_lkce_kdump

    def remove_lkce_kdump(self):
        return self.update_kdump_conf("--remove")
    # def remove_lkce_kdump()

    # enable lkce in /etc/kdump.conf
    def update_kdump_conf(self, arg):
        if not os.path.exists(self.KDUMP_CONF):
            print(
                "error: can not find %s. Please retry after installing kexec-tools") % (self.KDUMP_CONF)
            return 1

        KDUMP_PRE_LINE = f"kdump_pre {self.LKCE_KDUMP_SH}"
        KDUMP_TIMEOUT_LINE = f"extra_bins {self.TIMEOUT_PATH}"

        with open(self.KDUMP_CONF) as conf_fd:
            conf_lines = conf_fd.read().splitlines()

        kdump_pre_value = None
        for line in conf_lines:
            if line.startswith("kdump_pre "):
                kdump_pre_value = line

        if arg == "--remove":
            if kdump_pre_value != KDUMP_PRE_LINE:
                print(f"lkce_kdump entry not set in {self.KDUMP_CONF}")
                return 1

            # remove lkce_kdump config
            with open(self.KDUMP_CONF, "w") as conf_fd:
                for line in conf_lines:
                    if line not in (KDUMP_TIMEOUT_LINE, KDUMP_TIMEOUT_LINE):
                        conf_fd.write(f"{line}\n")

            self.restart_kdump_service()
            return 0

        # arg == "--add"
        if kdump_pre_value == KDUMP_PRE_LINE:
            print("lkce_kdump is already enabled to run lkce scripts")
        elif kdump_pre_value:
            # kdump_pre is enabled, but it is not our lkce_kdump script
            print(f"lkce_kdump entry not set in {self.KDUMP_CONF} "
                  "(manual setting needed)\n"
                  f"present entry in kdump.conf:\n{kdump_pre_value}\n"
                  "Hint: edit the present kdump_pre script and make it run"
                  f" {self.LKCE_KDUMP_SH}")
            return 1
        else:
            # add lkce_kdump config
            with open(self.KDUMP_CONF, "a") as conf_fd:
                conf_fd.write(
                    f"{KDUMP_PRE_LINE}\n{KDUMP_TIMEOUT_LINE}\n")
            self.restart_kdump_service()

        return 0
    # def update_kdump_conf

    def restart_kdump_service(self):
        cmd = ("systemctl", "restart", "kdump")  # OL7 and above

        print("Restarting kdump service...")
        subprocess.run(cmd, shell=False)  # nosec
        print("done!")
    # def restart_kdump_service

    def report(self, subargs):
        if not subargs:
            print(
                "error: report option need additional arguments [oled lkce help]")
            return

        vmcore = ""
        vmlinux = ""
        crash_cmds = None
        outfile = ""
        for subarg in subargs:
            subarg = re.sub(r"\s+", "", subarg)
            entry = re.split("=", subarg)
            if len(entry) < 2:
                print("error: unknown report option %s" % subarg)
                continue

            if "--vmcore" in entry[0]:
                vmcore = entry[1]

            elif "--vmlinux" in entry[0]:
                vmlinux = entry[1]

            elif "--crash_cmds" in entry[0]:
                crash_cmds = entry[1].split(",")
                crash_cmds.append("quit")

            elif "--outfile" in entry[0]:
                outfile = entry[1]

            else:
                print("error: unknown report option %s" % subarg)
                break
        # for

        if vmcore == "":
            print("error: vmcore not specified")
            return

        if vmlinux == "":
            vmlinux = self.vmlinux_path
        if not os.path.exists(vmlinux):
            print("error: %s not found" % vmlinux)
            return

        if crash_cmds is None:
            # use configured crash commands file
            if not os.path.exists(self.crash_cmds_file):
                print(f"{self.crash_cmds_file} not found")
                return

            cmd = ("crash", vmcore, vmlinux, "-i", self.crash_cmds_file)
            cmd_input = None
        else:
            # use specified crash commands
            cmd = ("crash", vmcore, vmlinux)
            cmd_input = "\n".join(crash_cmds).encode("utf-8")

        print("lkce: executing '{}'".format(" ".join(cmd)))

        if outfile:
            with open(outfile, "w") as output_fd:
                subprocess.run(
                    cmd, input=cmd_input, stdout=output_fd,
                    shell=False)  # nosec
        else:
            subprocess.run(
                cmd, input=cmd_input, stdout=sys.stdout, shell=False)  # nosec
    # def report

    def configure(self, subargs):
        if not subargs:  # default
            subargs = ["--show"]

        values_to_update = {}
        vmcore = None
        filename = self.LKCE_CONFIG_FILE
        for subarg in subargs:
            if subarg == "--default":
                self.configure_default()
            elif subarg == "--show":
                if not os.path.exists(filename):
                    print("config file not found")
                    return

                print("%15s : %s" % ("vmlinux path", self.vmlinux_path))
                print("%15s : %s" % ("crash_cmds_file", self.crash_cmds_file))
                print("%15s : %s " % ("vmcore", self.vmcore))
                print("%15s : %s" % ("lkce_outdir", self.lkce_outdir))
                print("%15s : %s" % ("lkce_in_kexec", self.enable_kexec))
                print("%15s : %s" % ("max_out_files", self.max_out_files))
            else:
                subarg = re.sub(r"\s+", "", subarg)
                entry = re.split("=", subarg)
                if len(entry) < 2:
                    print("error: unknown configure option %s" % subarg)
                    return

                if "--vmlinux_path" in entry[0]:
                    values_to_update["vmlinux_path"] = entry[1]
                elif "--crash_cmds_file" in entry[0]:
                    values_to_update["crash_cmds_file"] = entry[1]
                elif "--lkce_outdir" in entry[0]:
                    values_to_update["lkce_outdir"] = entry[1]
                elif "--vmcore" in entry[0]:
                    vmcore = entry[1]
                    values_to_update["vmcore"] = entry[1]
                elif "--max_out_files" in entry[0]:
                    values_to_update["max_out_files"] = entry[1]
                else:
                    print("error: unknown configure option %s" % subarg)
                    return
        # for

        if values_to_update:
            if vmcore and self.config_vmcore(vmcore):
                return

            update_key_values_file(filename, values_to_update, sep="=")
    # def configure

    def config_vmcore(self, value):
        if value not in ['yes', 'no']:
            print("error: invalid option '%s'") % (value)
            return 1

        filename = self.LKCE_KDUMP_SH
        if not os.path.exists(filename):
            print("error: Please enable lkce first, using 'oled lkce enable'")
            return 1

        self.vmcore = value
        self.create_lkce_kdump()
        self.restart_kdump_service()
        return 0
    # def config_vmcore

    def enable_lkce_kexec(self):
        if not os.path.exists(self.LKCE_KDUMP_SH):
            self.create_lkce_kdump()

        if self.update_kdump_conf("--add") == 1:
            return

        update_key_values_file(
            self.LKCE_CONFIG_FILE, {"enable_kexec": "yes"}, sep="=")
        print("enabled_kexec mode")
    # def enable_lkce_kexec

    def disable_lkce_kexec(self):
        if not os.path.exists(self.LKCE_CONFIG_FILE):
            print(f"config file '{self.LKCE_CONFIG_FILE}' not found")
            return

        if self.update_kdump_conf("--remove") == 1:
            return

        update_key_values_file(
            self.LKCE_CONFIG_FILE, {"enable_kexec": "no"}, sep="=")

        try:
            os.remove(self.LKCE_KDUMP_SH)
        except OSError:
            pass
        print("disabled kexec mode")
    # def disable kexec

    def status(self):
        self.configure(subargs=["--show"])
    # def status

    def clean(self, subarg):
        if "--all" in subarg:
            val = input(
                "lkce removes all the files in %s dir. do you want to proceed(yes/no)? [no]:" % self.LKCE_OUTDIR)
            if "yes" in val:
                for file in glob.glob(f"{self.LKCE_OUTDIR}/crash*out"):
                    try:
                        os.remove(file)
                    except OSError:
                        pass
            # if "yes"
        else:
            val = input(
                "lkce deletes all but last three %s/crash*out files. do you want to proceed(yes/no)? [no]:" % self.LKCE_OUTDIR)
            if "yes" in val:
                crash_files = glob.glob(f"{self.LKCE_OUTDIR}/crash*out")

                # remove all crash files but the 4 newest ones
                for file in sorted(crash_files, reverse=True)[4:]:
                    try:
                        os.remove(file)
                    except OSError:
                        pass
    # def clean

    def listfiles(self):
        dirname = self.LKCE_OUTDIR
        os.makedirs(dirname, exist_ok=True)

        print("Followings are the crash*out found in %s dir:" % dirname)
        for filename in os.listdir(dirname):
            if re.search("crash.*out", filename):
                print("%s/%s" % (dirname, filename))
        # for
    # def listfiles

    def usage(self):
        usage = """Usage: """ + os.path.basename(sys.argv[0]) + """ <options>
options:
	report <report-options> -- Generate a report from vmcore
	report-options:
		--vmcore=/path/to/vmcore 		- path to vmcore
		[--vmlinux=/path/to/vmlinux] 		- path to vmlinux
		[--crash_cmds=cmd1,cmd2,cmd3,..]	- crash commands to include
		[--outfile=/path/to/outfile] 		- write output to a file

	configure [--default] 	-- configure lkce with default values
	configure [--show] 	-- show lkce configuration -- default
	configure [config-options]
	config-options:
		[--vmlinux_path=/path/to/vmlinux] 	- set vmlinux_path
		[--crash_cmds_file=/path/to/file] 	- set crash_cmds_file
		[--vmcore=yes/no]			- set vmcore generation in kdump kernel
		[--lkce_outdir=/path/to/directory] 	- set lkce output directory
		[--max_out_files=<number>] 		- set max_out_files

	enable_kexec	-- enable lkce in kdump kernel
	disable_kexec   -- disable lkce in kdump kernel
	status 	        -- status of lkce

	clean [--all]	-- clear crash report files
	list		-- list crash report files
"""
        print(usage)
        sys.exit()
    # def usage
# class LKCE


def main():
    lkce = Lkce()

    if len(sys.argv) < 2:
        lkce.usage()

    arg = sys.argv[1]
    if arg == "report":
        lkce.report(sys.argv[2:])

    elif arg == "configure":
        lkce.configure(sys.argv[2:])

    elif arg == "enable_kexec":
        lkce.enable_lkce_kexec()

    elif arg == "disable_kexec":
        lkce.disable_lkce_kexec()

    elif arg == "status":
        lkce.status()

    elif arg == "clean":
        lkce.clean(sys.argv[2:])

    elif arg == "list":
        lkce.listfiles()

    elif arg == "help" or arg == "-help" or arg == "--help":
        lkce.usage()

    else:
        print("Invalid option: %s") % (arg)
        print("Try 'oled lkce help' for more information")
# def main


if __name__ == '__main__':
    if not os.geteuid() == 0:
        print("Please run lkce as root user.")
        sys.exit()

    lockdir = "/var/run/oled-tools"
    if not os.path.isdir(lockdir):
        os.makedirs(lockdir)
    lockfile = lockdir + "/lkce.lock"
    fh = open(lockfile, "w")
    try:  # try lock
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:  # no lock
        print("another instance of lkce is running.")
        sys.exit()

    main()

    fh.close()
    os.remove(lockfile)
