#!/usr/bin/python
#
# Copyright (c) 2020, Oracle and/or its affiliates.
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
# program to -
#	- generate kdump_pre.sh script
#
import commands, os, sys, re

class KDUMP_UTILS:
	def __init__(self):
		#global variables
		self.OLED_HOME = "/etc/oled"
		self.OLED_KDUMP_PRE_SH = self.OLED_HOME + "/kdump_pre.sh"
		self.OLED_KDUMP_PRE_DIR = self.OLED_HOME + "/kdump_pre.d"

		self.FSTAB = "/etc/fstab"
		self.KDUMP_CONF = "/etc/kdump.conf"

		#timeout
		self.TIMEOUT_PATH = commands.getoutput('which timeout')
	#def __init__

	def restart_kdump_service(self):
		cmd = "service kdump restart"
		os.system(cmd)
	#def restart_kdump_service

	def enable(self):
		filename = self.OLED_KDUMP_PRE_SH
		if not os.path.exists(filename):
			print("%s not found.  Run 'oled kdump --add' to create one")%(filename)
			return

		cmd = "sed -i 's/^OLED_ENABLE=.*/OLED_ENABLE=\"yes\"/' " + filename
		os.system(cmd);
		self.restart_kdump_service()
		print("enabled")
	#def enable

	def disable(self):
		filename = self.OLED_KDUMP_PRE_SH

		if not os.path.exists(filename):
			print("%s not found.  Run 'oled kdump --add' to create one")%(filename)
			return

		cmd = "sed -i 's/^OLED_ENABLE=.*/OLED_ENABLE=\"no\"/' " + filename
		os.system(cmd);
		self.restart_kdump_service()
		print("disabled")
	#def disable

	def status(self):
		filename = self.OLED_KDUMP_PRE_SH

		if not os.path.exists(filename):
			print("%s not found.  Run 'oled kdump --add' to create one")%(filename)
			return

		tmp_enable = ""
		tmp_vmcore = ""
		file = open(filename, "r")
		for line in file.readlines():
			#ignore lines starting with '#'
			if re.search("^#", line):
				continue

			#ignore lines not starting with 'OLED_'
			if not re.search("^OLED_", line):
				continue

			# trim space/tab/newline from the line
			line = re.sub(r"\s+", "", line)

                        entry = re.split("=", line)
                        if "OLED_ENABLE" in entry[0] and entry[1]:
                                tmp_enable = entry[1]

                        if "OLED_VMCORE" in entry[0] and entry[1]:
                                tmp_vmcore = entry[1]
		#for
		file.close()

		if "yes" in tmp_enable:
			print("kdump_scripts are enabled to run in kdump kernel")
		else:
			print("kdump_scripts are disabled to run in kdump kernel")

		if "yes" in tmp_vmcore:
			print("vmcore capture is enabled")
		else:
			print("vmcore capture is disabled")
	#def status

	def vmcore(self, arg):
		filename = self.OLED_KDUMP_PRE_SH

		if not os.path.exists(filename):
			print("%s not found.  Run 'oled kdump --add' to create one")%(filename)
			return

		if arg == "vmcore=yes":
			cmd = "sed -i 's/^OLED_VMCORE=.*/OLED_VMCORE=\"yes\"/' " + filename
		else:
			cmd = "sed -i 's/^OLED_VMCORE=.*/OLED_VMCORE=\"no\"/' " + filename

		os.system(cmd);
		self.restart_kdump_service()
	#def vmcore

	def create_kdump_pre(self):
		filename = self.OLED_KDUMP_PRE_SH

		#get the root device
		cmd = "awk '/^[ \t]*[^#]/ { if ($2 == \"/\") { print $1; }}' " + self.FSTAB
		rootdev= commands.getoutput(cmd)
		if "LABEL=" in rootdev or "UUID=" in rootdev :
			cmd = "/sbin/findfs " + rootdev
			rootdev = commands.getoutput(cmd)

		#create kdump_pre.sh script
		content = """#!/bin/sh
# This is a kdump_pre script
# /etc/kdump.conf is used to configure kdump_pre script

# status of executiong of kdump_pre scripts
OLED_ENABLE="yes"

# Generate vmcore post kdump_pre scripts execution
OLED_VMCORE="yes"

# Timeout for kdump_pre scripts in seconds
OLED_TIMEOUT="120"

# Temporary directory to mount the actual root partition
OLED_DIR="/oled"

if [ "$OLED_ENABLE" != "yes" ]; then
	echo "kdump_pre.sh: kdump_pre script execution disabled"
	if [ "$OLED_VMCORE" != "yes" ]; then
		echo "kdump_pre.sh: vmcore generation is disabled"
		exit 1
	fi

	exit 0
fi

mkdir $OLED_DIR
mount """ + rootdev + """ $OLED_DIR
mount -o bind /proc $OLED_DIR/proc
mount -o bind /dev $OLED_DIR/dev

KDUMP_PRE_SCRIPTS=$OLED_DIR""" + self.OLED_KDUMP_PRE_DIR + """/*

#get back control after $OLED_TIMEOUT to proceed
export KDUMP_PRE_SCRIPTS
export OLED_DIR
""" + self.TIMEOUT_PATH + """ $OLED_TIMEOUT /bin/sh -c '\\
echo "KDUMP_PRE_SCRIPTS=$KDUMP_PRE_SCRIPTS";\\
for file in $KDUMP_PRE_SCRIPTS;\\
do\\
        cmd=${file#$OLED_DIR};\\
        echo "Executing $cmd";\\
        chroot $OLED_DIR $cmd;\\
done;'

umount $OLED_DIR/dev
umount $OLED_DIR/proc
umount $OLED_DIR

unset KDUMP_PRE_SCRIPTS
unset OLED_DIR

if [ "$OLED_VMCORE" != "yes" ]; then
	echo "kdump_pre.sh: vmcore generation is disabled"
	exit 1
fi

exit 0
"""
		file = open(filename, "w")
		file.write(content)
		file.close()

		cmd = "chmod a+x " + filename
		os.system(cmd);
	#def create_kdump_pre

	#enable kdump_pre in /etc/kdump.conf
	def update_kdump_conf(self, arg):
		KUDMP_PRE_LINE = "kdump_pre " + self.OLED_KDUMP_PRE_SH
		KUDMP_TIMEOUT_LINE = "extra_bins " + self.TIMEOUT_PATH

		if arg == "--remove" :
			cmd = "sed --in-place '/""" + KUDMP_PRE_LINE.replace("/", "\/") + """/d' """ + self.KDUMP_CONF
			cmd = cmd + "; sed --in-place '/""" + KUDMP_TIMEOUT_LINE.replace("/", "\/") + """/d' """ + self.KDUMP_CONF
			print("%s")%(cmd)
			os.system(cmd)
			return

		#arg == "--add"
		cmd = "grep -q '^kdump_pre' " + self.KDUMP_CONF
		ret = os.system(cmd);
		if (ret): #not present
			cmd = "echo '" + KUDMP_PRE_LINE + "' >> " + self.KDUMP_CONF
			cmd = cmd + "; echo 'extra_bins " + self.TIMEOUT_PATH + "' >> " + self.KDUMP_CONF
			print("%s")%(cmd)
			os.system(cmd)
		else:
			cmd = "grep -q '^" +  KUDMP_PRE_LINE + "$' " + self.KDUMP_CONF
			if (os.system(cmd)): #kdump_pre is enabled, but it is not our kdump_pre script
				print("kdump_pre is already enabled. Manually enable the entry in %s")%(self.KDUMP_CONF)
				print("\nHint: you need to add the following")
				print("%s")%(KUDMP_PRE_LINE)
				print("%s\n")%(KUDMP_TIMEOUT_LINE)
				print("present entry in kdump.conf")
				cmd = "grep ^kdump_pre " + self.KDUMP_CONF
				os.system(cmd)
				return 1
			else:
				print("kdump_pre is already enabled to run oled scripts")
		return 0
	#def update_kdump_conf

	def usage(self):
		usage = """Usage: """ + sys.argv[0] + """ <options>
options:
	enable	-- enable oled kdump scripts
	disable	-- disable oled kdump scripts
	status	-- status of oled kdump scripts running in kdump kernel

	vmcore=yes	-- enable vmcore  generation
	vmcore=no	-- disable vmcore generaion

	--list		-- list the scripts in oled/kdump_pre.d directory

	help	-- print this info
"""
		print(usage)
		sys.exit()
	#def usage

#class KDUMP_UTILS

def main():
	ku = KDUMP_UTILS()

	if len(sys.argv) < 2:
		ku.usage()

	arg = sys.argv[1]
	if arg == "enable":
		ku.enable()

	elif arg == "disable":
		ku.disable()

	elif arg == "status":
		ku.status()

	elif arg == "vmcore=yes":
		ku.vmcore(arg)

	elif arg == "vmcore=no":
		ku.vmcore(arg)

	elif arg == "--add":
		cmd = "mkdir -p " + ku.OLED_KDUMP_PRE_DIR
		os.system(cmd)
		ku.create_kdump_pre()
		ku.update_kdump_conf(arg)

	elif arg == "--remove":
		ku.update_kdump_conf(arg)

	elif arg == "--list":
		print("list of oled kdump_pre scripts - ")
		cmd = "ls -lrt " + ku.OLED_KDUMP_PRE_DIR
		os.system(cmd)

	else:
		ku.usage()
#def main

if __name__ == '__main__':
	main()
