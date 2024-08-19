#!/usr/bin/env python3
#
# Copyright (c) 2023-2024, Oracle and/or its affiliates.
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

"""
Program for user-interaction
"""

import fcntl
import glob
import os
import platform
import re
import stat
import subprocess  # nosec
import sys
from typing import Mapping, Optional, List, Sequence


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


def read_args_from_file(filename: str) -> Optional[List[str]]:
    """Read command line arguments file and return the args as a list"""
    try:
        with open(filename, 'r') as f:
            args = [
                w.strip()
                for l in f
                for w in l.split()
                if not l.startswith('#')
            ]
            return args
    except OSError as e:
        print(f"kdump_report: Unable to operate on file: {filename}: {e}")
        return None


class Lkce:
    """Class to include user interaction related functionality"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self) -> None:
        """Constructor for Lkce class"""
        self.lkce_home = "/etc/oled/lkce"
        self.lkce_bindir = "/usr/lib/oled-tools"
        self.lkce_config_file = self.lkce_home + "/lkce.conf"
        self.kdump_kernel_ver = platform.uname().release
        self.vmcore = "yes"
        self.report_cmd = "corelens"
        self.lkce_outdir = "/var/oled/lkce"

        self.set_defaults()

        # set values from config file
        if os.path.exists(self.lkce_config_file):
            self.read_config(self.lkce_config_file)

        # lkce as a kdump_pre hook to kexec-tools
        self.lkce_kdump_sh = self.lkce_home + "/lkce_kdump.sh"
        self.lkce_kdump_dir = self.lkce_home + "/lkce_kdump.d"
        self.kdump_conf = "/etc/kdump.conf"
    # def __init__

    # default values
    def set_defaults(self) -> None:
        """set default values"""
        self.enable_kexec = "no"
        self.vmlinux_path = "/usr/lib/debug/lib/modules/" + \
            self.kdump_kernel_ver + "/vmlinux"
        self.crash_cmds_file = self.lkce_home + "/crash_cmds_file"
        self.corelens_args_file = self.lkce_home + "/corelens_args_file"
        self.corelens_default_args = ["-a"]
        self.vmcore = "yes"
        self.report_cmd = "corelens"
        self.max_out_files = "50"
        self.lkce_outdir = "/var/oled/lkce"
    # def set_default

    def configure_default(self) -> None:
        """Configure lkce with default values

        Creates self.corelens_args_file, self.crash_cmds_file,
        and self.lkce_config_file
        """
        os.makedirs(self.lkce_home, exist_ok=True)

        if self.enable_kexec == "yes":
            print("trying to disable lkce")
            self.disable_lkce_kexec()

        self.set_defaults()

        # crash_cmds_file
        filename = self.crash_cmds_file
        content = """#
# This is the input file for crash utility. You can edit this manually
# to add your own list of crash commands one per line.
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
        try:
            file = open(filename, "w")
            file.write(content)
            file.close()
        except OSError as e:
            print(f"error: Unable to operate on file: {filename}: {e}")
            return

        # corelens_args_file
        filename = self.corelens_args_file
        content = """#
# This is the input file for corelens utility. You can edit this manually
# to add your own list of corelens arguments.
#
-a
#-M inflight-io
#-M blockinfo
#-M ps
#-M bt
#-M meminfo
#-M buddyinfo
#-M cmdline
#-M cpuinfo
#-M dentrycache
#-M dm
#-M ext4_dirlock_scan
#-M filecache
#-M irq
#-M lock
#-M lsmod
#-M md
#-M mounts
#-M rds
#-M nfsshow
#-M numastat
#-M nvme
#-M partitioninfo
#-M dmesg
#-M runq
#-M scsiinfo
#-M slabinfo
#-M smp
#-M sys
#-M virtio
#-M wq
"""
        try:
            file = open(filename, "w")
            file.write(content)
            file.close()
        except OSError as e:
            print(f"error: Unable to operate on file: {filename}: {e}")
            return

        # config file
        filename = self.lkce_config_file
        content = """##
# This is the configuration file for lkce
# Use the 'oled lkce configure' command to change values
##

#report command to use for lkce
report_cmd=""" + self.report_cmd + """

#enable lkce in kexec kernel
enable_kexec=""" + self.enable_kexec + """

#debuginfo vmlinux path. Need to install debuginfo kernel to get it
vmlinux_path=""" + self.vmlinux_path + """

#path to file containing crash commands to execute
crash_cmds_file=""" + self.crash_cmds_file + """

#path to file containing corelens command line arguments
corelens_args_file=""" + self.corelens_args_file + """

#lkce output directory path
lkce_outdir=""" + self.lkce_outdir + """

#enable vmcore generation post kdump_report
vmcore=""" + self.vmcore + """

#maximum number of outputfiles to retain. Older file gets deleted
max_out_files=""" + self.max_out_files

        try:
            file = open(filename, "w")
            file.write(content)
            file.close()
        except OSError:
            print("Unable to operate on file: {filename}")
            return

        print("configured with default values")
    # def configure_default

    def read_config(self, filename: str) -> None:
        """Read config file and update the class variables"""
        if not os.path.exists(filename):
            return

        try:
            file = open(filename, "r")
        except OSError:
            print("Unable to open file: {filename}")
            return

        for line in file.readlines():
            if re.search("^#", line):  # ignore lines starting with '#'
                continue

            # trim space/tab/newline from the line
            line = re.sub(r"\s+", "", line)

            entry = re.split("=", line)
            if "enable_kexec" in entry[0] and entry[1]:
                self.enable_kexec = entry[1]

            elif "report_cmd" in entry[0] and entry[1]:
                self.report_cmd = entry[1]

            elif "corelens_args_file" in entry[0] and entry[1]:
                self.corelens_args_file = entry[1]

            elif "crash_cmds_file" in entry[0] and entry[1]:
                self.crash_cmds_file = entry[1]

            elif "lkce_outdir" in entry[0] and entry[1]:
                self.lkce_outdir = entry[1]

            elif "vmlinux_path" in entry[0] and entry[1]:
                self.vmlinux_path = entry[1]

            elif "vmcore" in entry[0] and entry[1]:
                self.vmcore = entry[1]

            elif "max_out_files" in entry[0] and entry[1]:
                self.max_out_files = entry[1]
    # def read_config

    def create_lkce_kdump(self) -> None:
        """create lkce_kdump.sh script.

        lkce_kdump.sh is attached as kdump_pre hook in /etc/kdump.conf
        """
        filename = self.lkce_kdump_sh
        os.makedirs(self.lkce_kdump_dir, exist_ok=True)

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

LKCE_KDUMP_SCRIPTS=""" + self.lkce_kdump_dir + """/*

#get back control after $LKCE_TIMEOUT to proceed
export LKCE_KDUMP_SCRIPTS
export LKCE_DIR
export LKCE_TIMEOUT

chroot $LKCE_DIR /usr/bin/timeout -k 2 $LKCE_TIMEOUT /bin/sh -c '
echo "LKCE_KDUMP_SCRIPTS=$LKCE_KDUMP_SCRIPTS";
for cmd in $LKCE_KDUMP_SCRIPTS;
do
    echo "Executing $cmd";
    $cmd;
done;'

umount $LKCE_DIR/dev
umount $LKCE_DIR/proc
umount $LKCE_DIR

unset LKCE_KDUMP_SCRIPTS
unset LKCE_DIR
unset LKCE_TIMEOUT

if [ "$LKCE_VMCORE" == "no" ]; then
    echo "lkce_kdump.sh: vmcore generation is disabled"
    exit 1
fi

exit 0
"""
        try:
            file = open(filename, "w")
            file.write(content)
            file.close()
        except OSError:
            print("Unable to operate on file: {filename}")
            return

        mode = os.stat(filename).st_mode
        os.chmod(filename, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # def create_lkce_kdump

    def remove_lkce_kdump(self) -> int:
        """Remove lkce_kdump.sh as kdump_pre hook in /etc/kdump.conf"""
        return self.update_kdump_conf("--remove")
    # def remove_lkce_kdump()

    def update_kdump_conf(self, arg: str) -> int:
        """Add/remove /etc/kdump.conf with kdump_pre hook"""
        if not os.path.exists(self.kdump_conf):
            print(f"error: can not find {self.kdump_conf}. "
                  "Please retry after installing kexec-tools")
            return 1

        kdump_pre_line = f"kdump_pre {self.lkce_kdump_sh}"

        with open(self.kdump_conf) as conf_fd:
            conf_lines = conf_fd.read().splitlines()

        kdump_pre_value = None
        for line in conf_lines:
            if line.startswith("kdump_pre "):
                kdump_pre_value = line

        if arg == "--remove":
            if kdump_pre_value != kdump_pre_line:
                print(f"lkce_kdump entry not set in {self.kdump_conf}")
                return 1

            # remove lkce_kdump config
            with open(self.kdump_conf, "w") as conf_fd:
                for line in conf_lines:
                    if line != kdump_pre_line:
                        conf_fd.write(f"{line}\n")

            restart_kdump_service()
            return 0

        # arg == "--add"
        if kdump_pre_value == kdump_pre_line:
            print("lkce_kdump is already enabled to run lkce scripts")
        elif kdump_pre_value:
            # kdump_pre is enabled, but it is not our lkce_kdump script
            print(f"lkce_kdump entry not set in {self.kdump_conf} "
                  "(manual setting needed)\n"
                  f"present entry in kdump.conf:\n{kdump_pre_value}\n"
                  "Hint: edit the present kdump_pre script and make it run"
                  f" {self.lkce_kdump_sh}")
            return 1
        else:
            # add lkce_kdump config
            with open(self.kdump_conf, "a") as conf_fd:
                conf_fd.write(
                    f"{kdump_pre_line}\n")
            restart_kdump_service()

        return 0
    # def update_kdump_conf

    def report(self, subargs: List[str]) -> None:
        """Generate report from vmcore"""
        if not subargs:
            print("error: report option needs additional arguments "
                  "[oled lkce help]")
            return

        d_subargs = {}
        for subarg in subargs:
            subarg.strip()
            entry = subarg.split("=", 1)

            if len(entry) < 2:
                print(f"error: unknown report option: {subarg}")
                continue

            if entry[0] not in ("--vmcore", "--vmlinux", "--report_cmd",
                                "--crash_cmds", "--corelens_args_file",
                                "--outfile"):

                print(f"error: unknown report option: {entry[0]}")
                break

            d_subargs[entry[0].strip()] = entry[1].strip()
        # for

        vmcore = d_subargs.get("--vmcore", None)
        outfile = d_subargs.get("--outfile", None)

        if vmcore is None:
            print("error: vmcore not specified")
            return

        if self.report_cmd == "crash":
            vmlinux = d_subargs.get("--vmlinux", None)
            if vmlinux is None:
                vmlinux = self.vmlinux_path

            if not os.path.isfile(vmlinux):
                print(f"error: vmlinux '{vmlinux}' not found")
                return

            crash_cmds = d_subargs.get("--crash_cmds", None)

            if crash_cmds is None:
                # use configured crash commands file
                if not os.path.isfile(self.crash_cmds_file):
                    print(
                        f"crash_cmds_file '{self.crash_cmds_file}' not found")
                    return
                cmd: Sequence[str] = ("crash", vmcore, vmlinux, "-i",
                                      self.crash_cmds_file)
                cmd_input = None
            else:
                # use specified crash commands
                cmd = ("crash", vmcore, vmlinux)
                crash_cmds = crash_cmds + "," + "quit"
                cmd_input = "\n".join(crash_cmds.split(",")).encode("utf-8")

            print("lkce: executing '{}'".format(" ".join(cmd)))

            if outfile:
                with open(outfile, "w") as output_fd:
                    subprocess.run(
                        cmd, input=cmd_input, stdout=output_fd, check=True,
                        shell=False)  # nosec
            else:
                subprocess.run(
                    cmd, input=cmd_input, stdout=sys.stdout, check=True,
                    shell=False)  # nosec
        elif self.report_cmd == "corelens":
            corelens_args_file = d_subargs.get("--corelens_args_file", None)

            cmd: List[str] = ["corelens", vmcore]
            if corelens_args_file is None:
                # use configured corelens arguments file
                if not os.path.isfile(self.corelens_args_file):
                    print(f"corelens_args_file '{self.corelens_args_file}' "
                          "not found")
                else:
                    corelens_args_file = self.corelens_args_file

            if corelens_args_file is None:
                cmd.extend(self.corelens_default_args)
            else:
                # use specified corelens arguments file
                corelens_args = read_args_from_file(corelens_args_file)
                if corelens_args is None:
                    cmd.extend(self.corelens_default_args)
                else:
                    cmd.extend(corelens_args)

            print("lkce: executing '{}'".format(" ".join(cmd)))

            if outfile:
                with open(outfile, "w") as output_fd:
                    subprocess.run(
                        cmd, stdout=output_fd, check=True,
                        shell=False)  # nosec
            else:
                subprocess.run(
                    cmd, stdout=sys.stdout, check=True,
                    shell=False)  # nosec
        else:
            print(f"lkce: error: Unknown report command: {self.report_cmd}")
    # def report

    def configure(self, subargs: List[str]) -> None:
        """Configure lkce

        Based on subarg, you can configure with default values, show the values
        and also set to given values
        """
        if not subargs:  # default
            subargs = ["--show"]

        values_to_update = {}
        filename = self.lkce_config_file
        for subarg in subargs:
            subarg.strip()
            if subarg == "--default":
                self.configure_default()
            elif subarg == "--show":
                if not os.path.exists(filename):
                    print("config file not found")
                    return

                print("%18s : %s" % ("report_cmd", self.report_cmd))
                print("%18s : %s" %
                      ("corelens_args_file", self.corelens_args_file))
                print("%18s : %s" % ("vmcore", self.vmcore))
                print("%18s : %s" % ("vmlinux path", self.vmlinux_path))
                print("%18s : %s" % ("crash_cmds_file", self.crash_cmds_file))
                print("%18s : %s" % ("lkce_outdir", self.lkce_outdir))
                print("%18s : %s" % ("lkce_in_kexec", self.enable_kexec))
                print("%18s : %s" % ("max_out_files", self.max_out_files))
            else:
                entry = subarg.split("=", 1)

                if len(entry) < 2:
                    print(f"error: no value given for option {subarg}")
                    return

                if entry[0] not in ("--corelens_args_file",
                                    "--crash_cmds_file",
                                    "--vmlinux", "--report_cmd",
                                    "--lkce_outdir", "--vmcore",
                                    "--max_out_files"):
                    print(f"error: unknown configure option: {subarg}")
                    return

                values_to_update[entry[0].strip("-")] = entry[1].strip()
        # for

        report_cmd = values_to_update.get("report_cmd", None)
        if report_cmd and self.config_report_cmd(report_cmd):
            return

        vmcore = values_to_update.get("vmcore", None)
        if vmcore and self.config_vmcore(vmcore):
            return

        lkce_outdir = values_to_update.get("lkce_outdir", None)
        if lkce_outdir and self.config_lkce_outdir(lkce_outdir):
            return

        if values_to_update:
            update_key_values_file(filename, values_to_update, sep="=")
    # def configure

    def config_vmcore(self, value: str) -> int:
        """Configure vmcore value in lkce_config_file.

        Called from configure()
        """
        if value not in ['yes', 'no']:
            print(f"error: invalid option '{value}'")
            return 1

        filename = self.lkce_kdump_sh
        if not os.path.exists(filename):
            print("error: Please enable lkce first using",
                  "'oled lkce enable_kexec'")
            return 1

        self.vmcore = value
        self.create_lkce_kdump()
        restart_kdump_service()
        return 0
    # def config_vmcore

    def config_report_cmd(self, value: str) -> int:
        """Configure the report command.

        Called from configure()
        """
        value = value.lower()
        if value != "corelens":
            print(f"error: Invalid report command specified: '{value}'",
                  "\nCurrently, only 'corelens' is supported.")
            return 1
        self.report_cmd = value
        return 0
    # def config_report_cmd

    def config_lkce_outdir(self, value: str) -> int:
        """Configure lkce_outdir value in lkce_config_file.

        Called from configure()
        """
        filename = self.lkce_kdump_sh
        if not os.path.exists(filename):
            print("error: Please enable lkce first using",
                  "'oled lkce enable_kexec'")
            return 1

        # Re-generate the pre-kexec hook script in case the location of the
        # output directory is not on the root filesystem and it needs to be
        # made available in kexec mode.
        self.lkce_outdir = value
        self.create_lkce_kdump()
        restart_kdump_service()
        return 0
    # def config_lkce_outdir

    def enable_lkce_kexec(self) -> None:
        """Enable lkce to generate report on crashed kernel in kexec mode"""
        if not os.path.exists(self.lkce_kdump_sh):
            self.create_lkce_kdump()

        if self.update_kdump_conf("--add") == 1:
            return

        update_key_values_file(
            self.lkce_config_file, {"enable_kexec": "yes"}, sep="=")
        print("enabled_kexec mode")
    # def enable_lkce_kexec

    def disable_lkce_kexec(self) -> None:
        """Disable lkce to generate report on crashed kernel in kexec mode"""
        if not os.path.exists(self.lkce_config_file):
            print(f"config file '{self.lkce_config_file}' not found")
            return

        if self.update_kdump_conf("--remove") == 1:
            return

        update_key_values_file(
            self.lkce_config_file, {"enable_kexec": "no"}, sep="=")

        try:
            os.remove(self.lkce_kdump_sh)
        except OSError:
            pass
        print("disabled kexec mode")
    # def disable kexec

    def status(self) -> None:
        """Show current configuration values"""
        self.configure(subargs=["--show"])

        if self.report_cmd == "crash":
            pkg = "crash"
        else:
            pkg = "drgn-tools"

        r = subprocess.run(("rpm", "-q", pkg), shell=False,  # nosec
                           check=False)
        if r.returncode != 0:
            print(f"NOTE: The {pkg} package is not installed.")
    # def status

    def clean(self, subarg: List[str]) -> None:
        """Clean up old crash and corelens reports to save space"""
        report_files = []
        for p in ("crash*.out", "corelens*.out"):
            report_files.extend(glob.glob(f"{self.lkce_outdir}/{p}"))

        if "--all" in subarg:
            val = input("lkce will delete all the"
                        f"{self.lkce_outdir}/crash*.out and "
                        f"{self.lkce_outdir}/corelens*.out files.\n"
                        "Do you want to proceed? (yes/no) [no]: ")
            if "yes" not in val:
                return
        else:
            val = input("lkce will delete all but the last",
                        f"{self.max_out_files} {self.lkce_outdir}/crash*.out",
                        f"and {self.lkce_outdir}/corelens*.out files.\n"
                        "Do you want to proceed? (yes/no) [no]: ")
            if "yes" not in val:
                return

            # select all crash/corelens files but the N newest ones
            # where N == self.max_out_files
            report_files.sort(
                key=lambda x: os.path.getctime(x), reverse=True)
            report_files = report_files[int(self.max_out_files):]

        for f in report_files:
            try:
                os.remove(f)
            except OSError as e:
                print(f"error: Unable to remove {f}: {e}")
    # def clean

    def listfiles(self) -> None:
        """List corelens reports already generated"""
        dirname = self.lkce_outdir
        os.makedirs(dirname, exist_ok=True)

        print(f"The following are the reports found in {dirname}:")
        for filename in os.listdir(dirname):
            if re.search("(crash|corelens).*out", filename):
                print(f"{dirname}/{filename}")
    # def listfiles

# class LKCE


def restart_kdump_service() -> int:
    """Restart kdump service"""
    cmd = ("systemctl", "restart", "kdump")  # OL7 and above

    print("Restarting kdump service...")
    r = subprocess.run(cmd, shell=False, check=True)  # nosec
    print("done!")
    return r.returncode
# def restart_kdump_service


def usage() -> int:
    """Print usage"""
    usage_ = """Usage: """ + os.path.basename(sys.argv[0]) + """ <options>
options:
    report <report-options> -- Generate a report from vmcore
    report-options:
        --vmcore=/path/to/vmcore 		- path to vmcore
        [--vmlinux=/path/to/vmlinux]            - path to vmlinux
        [--crash_cmds=cmd1,cmd2,cmd3,..]        - crash commands to run
        [--corelens_args_file=/path/to/file]	- path to corelens arguments file
        [--outfile=/path/to/outfile] 		- write output to a file

    configure [--default] 	-- configure lkce with default values
    configure [--show] 	-- show lkce configuration -- default
    configure [config-options]
    config-options:
        [--vmlinux_path=/path/to/vmlinux]       - set vmlinux_path
        [--crash_cmds_file=/path/to/file]       - set crash_cmds_file
        [--corelens_args_file=/path/to/file] 	- set corelens_args_file
        [--vmcore=yes/no]			- set vmcore generation in kdump kernel
        [--lkce_outdir=/path/to/directory] 	- set lkce output directory
        [--max_out_files=<number>] 		- set max_out_files

    enable_kexec    -- enable lkce in kdump kernel
    disable_kexec   -- disable lkce in kdump kernel
    status          -- status of lkce

    clean [--all]   -- clear crash/corelens report files
    list            -- list crash/corelens report files
"""
    print(usage_)
    sys.exit(0)
# def usage


def main() -> int:
    """Main routine"""
    lkce = Lkce()

    if len(sys.argv) < 2:
        usage()

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

    elif arg in ("help", "-help", "--help", "-h"):
        usage()

    else:
        print(f"Invalid option: {arg}")
        print("Try 'oled lkce help' for more information")

    return 0
# def main


if __name__ == '__main__':
    if not os.geteuid() == 0:
        print("Please run lkce as root user.")
        sys.exit(1)

    LOCK_DIR = "/var/run/oled-tools"
    try:
        if not os.path.isdir(LOCK_DIR):
            os.makedirs(LOCK_DIR)
        LOCK_FILE = LOCK_DIR + "/lkce.lock"

        FH = open(LOCK_FILE, "w")
    except OSError:
        print(f"Unable to open file: {LOCK_FILE}")
        sys.exit()

    # try lock
    try:
        fcntl.flock(FH, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:  # no lock
        print("error: another instance of lkce is running.")
        sys.exit()

    try:
        main()
        FH.close()
        os.remove(LOCK_FILE)
    except KeyboardInterrupt:
        print("\nInterrupted by user ctrl+c")
