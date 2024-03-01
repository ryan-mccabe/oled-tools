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
Program that runs inside kdump kernel
Program to run corelens utility inside the kdump kernel
"""
import glob
import time
import os
import platform
import re
import shutil
import subprocess  # nosec
import sys
from typing import Optional, List


class KdumpReport:
    """Class to include all kdump report related functionality"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        """Constructor for KdumpReport class"""
        self.vmcore = "/proc/vmcore"
        self.kdump_kernel_ver = platform.uname().release

        self.kdump_report_home = "/etc/oled/lkce"
        self.kdump_report_config_file = self.kdump_report_home + "/lkce.conf"
        self.kdump_report_corelens_args_file = self.kdump_report_home + \
            "/corelens_args_file"
        self.kdump_report_out = "/var/oled/lkce"
        self.kdump_report_out_file = self.kdump_report_out + \
            "/corelens_" + time.strftime("%Y%m%d-%H%M%S") + ".out"
        self.timedout_action = "reboot -f"

        # default values
        self.kdump_report = "yes"
        self.corelens_args_file = self.kdump_report_corelens_args_file
        self.max_out_files = "50"
        self.corelens_args = ["-a"]

        self.read_config(self.kdump_report_config_file)
    # def __init__

    def read_config(self, filename: str) -> int:
        """Read config file and update the class variables"""
        if not os.path.exists(filename):
            sys.exit(1)

        try:
            file = open(filename, "r")
        except OSError:
            print(f"kdump_report: Unable to operate on file: {filename}")
            return 1

        for line in file.readlines():
            if re.search("^#", line):  # ignore lines starting with '#'
                continue

            # trim space/tab/newline from the line
            line = re.sub(r"\s+", "", line)

            entry = re.split("=", line)

            if "corelens_args_file" in entry[0] and entry[1]:
                self.corelens_args_file = entry[1]

            elif "enable_kexec" in entry[0] and entry[1]:
                self.kdump_report = entry[1]

            elif "max_out_files" in entry[0] and entry[1]:
                self.max_out_files = entry[1]

        return 0
    # def read_config

    def read_args(self, filename: str) -> Optional[List[str]]:
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
        except Exception as e:
            print(f"kdump_report: Unable to operate on file: {filename}: {e}")
            return None
    # def read_args

    def run_corelens(self) -> int:
        """Run corelens utility against vmcore"""
        corelens_path = shutil.which("corelens")

        if not corelens_path:
            print("kdump_report: 'corelens' executable not found")
            return 1

        os.makedirs(self.kdump_report_out, exist_ok=True)

        args = [corelens_path, self.vmcore]
        corelens_args = self.read_args(self.corelens_args_file)
        if corelens_args:
            args.extend(corelens_args)
        else:
            args.extend(self.corelens_args)
        print(f"kdump_report: Executing '{' '.join(args)}'; output file "
              f"'{self.kdump_report_out_file}'")

        with open(self.kdump_report_out_file, "w") as output_fd:
            subprocess.run(args, close_fds=True, stdout=output_fd,
                           stderr=output_fd, stdin=subprocess.DEVNULL,
                           shell=False, check=True)  # nosec
        return 0
    # def run_corelens

    def clean_up(self) -> None:
        """Clean up old corelens reports to save space"""
        max_files = int(self.max_out_files)
        corelens_files = glob.glob(f"{self.kdump_report_out}/corelens*out")

        if len(corelens_files) > max_files:
            print(f"kdump_report: found more than {max_files}[max_out_files] "
                  "out files. Deleting older ones")

            for file in sorted(corelens_files, reverse=True)[max_files:]:
                try:
                    os.remove(file)
                except OSError:
                    pass  # ignore permissions and missing file errors
    # def clean_up
# class KDUMP_REPORT


def main() -> int:
    """Main routine"""
    kdump_report = KdumpReport()

    if kdump_report.kdump_report != "yes":
        print("kdump_report: kdump_report is disabled to run")
        sys.exit(1)
    else:
        print("kdump_report: kdump_report is enabled to run")
        kdump_report.run_corelens()
        kdump_report.clean_up()
        sys.exit(0)
# def main


if __name__ == '__main__':
    main()
