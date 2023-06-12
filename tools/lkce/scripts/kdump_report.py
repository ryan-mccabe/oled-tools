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
# program that runs inside kdump kernel
# program to run crash utility inside the kdump kernel
#
import glob
import time
import os
import platform
import re
import shutil
import subprocess  # nosec
import sys
import signal

class KdumpReport:
	def __init__(self):
		#global variables
		self.VMLINUX = ""
		self.VMCORE = "/proc/vmcore"
		self.KDUMP_KERNELVER = platform.uname().release

		self.KDUMP_REPORT_HOME = "/etc/oled/lkce"
		self.KDUMP_REPORT_CONFIG_FILE = self.KDUMP_REPORT_HOME + "/lkce.conf"
		self.KDUMP_REPORT_CRASH_CMDS_FILE = self.KDUMP_REPORT_HOME + "/crash_cmds_file"
		self.KDUMP_REPORT_OUT = "/var/oled/lkce"
		self.KDUMP_REPORT_OUT_FILE = self.KDUMP_REPORT_OUT + "/crash_" + time.strftime("%Y%m%d-%H%M%S") + ".out"
		self.TIMEDOUT_ACTION = "reboot -f"

		# default values
		self.kdump_report = "yes"
		self.vmlinux_path = "/usr/lib/debug/lib/modules/" + self.KDUMP_KERNELVER + "/vmlinux"
		self.crash_cmds_file = self.KDUMP_REPORT_CRASH_CMDS_FILE
		self.max_out_files = "50"

		self.read_config(self.KDUMP_REPORT_CONFIG_FILE)
	# def __init__

	def read_config(self, filename):
		if not os.path.exists(filename):
			self.exit()

		try:
			file = open(filename, "r")
		except:
			print("kdump_report: Unable to operate on file: %s" % (filename))
			return

		for line in file.readlines():
			if re.search("^#", line):# ignore lines starting with '#'
				continue

			# trim space/tab/newline from the line
			line = re.sub(r"\s+", "", line)

			entry = re.split("=", line)
			if "vmlinux_path" in entry[0] and entry[1]:
				self.vmlinux_path = entry[1]

			elif "crash_cmds_file" in entry[0] and entry[1]:
				self.crash_cmds_file = entry[1]

			elif "enable_kexec" in entry[0] and entry[1]:
				self.kdump_report = entry[1]

			elif "max_out_files" in entry[0] and entry[1]:
				self.max_out_files = entry[1]
	#def read_config

	def get_vmlinux(self):
		VMLINUX_1 = self.vmlinux_path
		VMLINUX_2 = "/usr/lib/debug/lib/modules/" + self.KDUMP_KERNELVER + "/vmlinux"

		if os.path.exists(VMLINUX_1):
			self.VMLINUX = VMLINUX_1
		elif os.path.exists(VMLINUX_2):
			self.VMLINUX = VMLINUX_2
		else:
			print("kdump_report: vmlinux not found in the following locations.")
			print("kdump_report: %s" % VMLINUX_1)
			print("kdump_report: %s" % VMLINUX_2)
			self.exit()

		print("kdump_report: vmlinux found at %s" % self.VMLINUX)
	# def get_vmlinux

	def run_crash(self):
		crash_path = shutil.which("crash")

		if not crash_path:
			print("kdump_report: 'crash' executable not found")
			return 1

		self.get_vmlinux()
		if not os.path.exists(self.crash_cmds_file):
			print("kdump_report: %s not found" % self.crash_cmds_file)
			return 1

		os.makedirs(self.KDUMP_REPORT_OUT, exist_ok=True)

		args = (crash_path, self.VMLINUX, self.VMCORE, "-i",
		        self.crash_cmds_file)
		print(f"kdump_report: Executing '{' '.join(args)}'; output file "
		      f"'{self.KDUMP_REPORT_OUT_FILE}'")

		with open(self.KDUMP_REPORT_OUT_FILE, "w") as output_fd:
			return subprocess.run(
				args, close_fds=True, stdout=output_fd, stderr=output_fd,
				stdin=subprocess.DEVNULL, shell=False)  #nosec
	# def run_crash

	def clean_up(self):
		max_files = int(self.max_out_files)
		crash_files = glob.glob(f"{self.KDUMP_REPORT_OUT}/crash*out")

		if len(crash_files) > max_files:
			print(f"kdump_report: found more than {max_files}[max_out_files] "
			      "out files. Deleting older ones")

			for file in sorted(crash_files, reverse=True)[max_files:]:
				try:
					os.remove(file)
				except OSError:
					pass  # ignore permissions and missing file errors
	# def clean_up

	def exit(self):
		sys.exit(0)
	# def exit

# class KDUMP_REPORT

def main():
	kdump_report = KdumpReport()

	if kdump_report.kdump_report != "yes":
		print("kdump_report: kdump_report is disabled to run")
		kdump_report.exit()
	else:
		print("kdump_report: kdump_report is enabled to run")
		kdump_report.run_crash()
		kdump_report.clean_up()
		kdump_report.exit()
# def main

if __name__ == '__main__':
	main()
