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
# program for user-interaction
# program to enable/disable/configure/... lkce
#
import sys, commands, os, re

class LKCE:
	def __init__(self):
		#global variables
		self.LKCE_HOME = "/etc/oled/lkce"
		self.LKCE_CONFIG_FILE = self.LKCE_HOME + "/lkce.conf"
		self.LKCE_CRASH_CMDS_FILE = self.LKCE_HOME + "/crash_cmds"
		self.LKCE_OUT="/var/crash/lkce"

		self.SYSCONFIG_KDUMP = "/etc/sysconfig/kdump"
		self.KDUMP_KERNELVER = commands.getoutput('uname -r')

		#vmlinux_path
		file = open(self.SYSCONFIG_KDUMP, "r")
		for line in file:
			if re.search("KDUMP_KERNELVER=", line):
				line = re.sub(r"\s+", "", line)
				entry = re.split("=", line)
				if re.search("\w", entry[1]):
					self.KDUMP_KERNELVER = entry[1]
			#if re.seach
		#for
		file.close()

		#default values
		self.enable = "yes"
		self.vmlinux_path = "/usr/lib/debug/lib/modules/" + self.KDUMP_KERNELVER
		self.crash_cmds_file = self.LKCE_CRASH_CMDS_FILE
		self.max_out_files = "50"

		if not os.path.isdir(self.LKCE_HOME):
			os.mkdir(self.LKCE_HOME)

		self.LKCE_KDUMP_PRE_LINK = "/etc/oled/kdump_pre.d/lkce-kdump"
		BINDIR="/sbin/oled-tools"
		if not os.path.exists(BINDIR):
		        BINDIR="/usr/sbin/oled-tools"
		self.LKCE_KDUMP_PRE_SCRIPT = BINDIR + "/lkce-kdump"
	#def __init__

	def create_crash_cmds_file(self, filename):
		content = """#
# This is the input file for crash utility. You can edit this manually
# Add your own list of crash commands one per line.
#
bt
bt -FF
bt -a
foreach bt
log
ps -m
kmem -i
quit
"""
		file = open(filename, "w")
		file.write(content)
		file.close()
	#def create_crash_cmds_file

	def show_config(self, filename):
		if not os.path.exists(filename):
			print "%s not found.  Run 'oled lkce configure' to create one"%(filename)
			return

		print "Filename: %s"%(filename)
		file = open(filename, "r")
		for line in file.readlines():
			print line,
		file.close()
	#def show_config

	def read_config(self, filename):
		if not os.path.exists(filename):
			return

		file = open(filename, "r")
		for line in file.readlines():
			if re.search("^#", line): #ignore lines starting with '#'
				continue

			# trim space/tab/newline from the line
			line = re.sub(r"\s+", "", line)

			entry = re.split("=", line)
			if "enable" in entry[0] and entry[1]:
				self.enable = entry[1]

			elif "vmlinux_path" in entry[0] and entry[1]:
				self.vmlinux_path = entry[1]

			elif "crash_cmds_file" in entry[0] and entry[1]:
				self.crash_cmds_file = entry[1]

			elif "max_out_files" in entry[0] and entry[1]:
				self.max_out_files = entry[1]
	#def read_config

	# maintain this call sequence: read_config();ask_user();write_config()
	def ask_user(self):
		val = raw_input("enable lkce? values(yes,no)[%s]:"%self.enable)
		if "yes" in val or "no" in val:
			self.enable = val

		val = raw_input("Enter the path to debuginfo vmlinux[%s]:"%self.vmlinux_path)
		if val:
			self.vmlinux_path = val

		val = raw_input("Enter the path to file containing crash commands[%s]:"%self.crash_cmds_file)
		if val:
			self.crash_cmds_file = val

		val = raw_input("Enter number of output files to retain[%s]:"%self.max_out_files)
		if val:
			self.max_out_files = val
	#def ask_user

	def write_config(self, filename):
		content = """##
# This is configuration file for lkce
# You can edit manually. Recommended way is to run 'oled lkce configure'
##

#enable/disable(yes,no) lkce script in kdump kernel
enable=""" + self.enable + """

#debuginfo vmlinux path. Need to install debuginfo kernel to get it
vmlinux_path=""" + self.vmlinux_path + """

#path to file containing crash commands to execute
crash_cmds_file=""" + self.crash_cmds_file + """

#maximum number of outputfiles to retain. Older file gets deleted
max_out_files=""" + self.max_out_files

		file = open(filename, "w")
		file.write(content)
		file.close()

		print "wrote the values into %s"%filename
	#def write_config

	def check_config(self, filename):
		if not os.path.exists(filename):
			print "%s not found.  Run 'oled lkce configure' to create one"%(filename)
			return

		self.read_config(filename)
		proper_config = True

		if self.enable == "yes":
			print "lkce is enabled to run.",
		else:
			print "NOTICE: lkce is disabled to run [to enable:'oled lkce enable'].",
			proper_config = False

		vmlinux_conf = self.vmlinux_path + "/vmlinux"
		if os.path.exists(vmlinux_conf):
			tmp_path = self.LKCE_OUT + "/debug-vmlinux/" + self.KDUMP_KERNELVER + "/"
			cmd1 = "mkdir -p " + tmp_path
			cmd2 = "cp " + vmlinux_conf + " " + tmp_path
			os.system(cmd1)
			os.system(cmd2)
			print "vmlinux found at: %s."%(vmlinux_conf),
		else:
			print "\nNOTICE: vmlinux not found.",
			print "did you install debuginfo kernel package?",
			print "correct the error and rerun 'oled lkce configure'.",
			proper_config = False

		if proper_config == True:
			print "configuration is correct"
		else:
			print "configuration is incorrect"

	#def check_config

###########################################
# lkce option related functions
###########################################

	def enable_lkce(self):
		filename = self.LKCE_CONFIG_FILE

		if not os.path.exists(filename):
			print "%s not found.  Run 'oled lkce configure' to create one"%(filename)
			return

		cmd = "sed -i 's/enable=.*/enable=yes/' " + filename
		os.system(cmd);
		print "enabled"
	#def enable_lkce

	def disable_lkce(self):
		filename = self.LKCE_CONFIG_FILE

		if not os.path.exists(filename):
			print "%s not found.  Run 'oled lkce configure' to create one"%(filename)
			return

		cmd = "sed -i 's/enable=.*/enable=no/' " + filename
		os.system(cmd);
		print "disabled"
	#def disable_lkce

	def configure(self, subarg):
		if subarg == "--show":
			self.show_config(self.LKCE_CONFIG_FILE)
			return
		elif subarg == "--default":
			self.create_crash_cmds_file(self.LKCE_CRASH_CMDS_FILE)
		else:
			self.read_config(self.LKCE_CONFIG_FILE)
			self.ask_user()

		self.write_config(self.LKCE_CONFIG_FILE)
		print "checking configuration"
		self.check_config(self.LKCE_CONFIG_FILE)

		# create a link to lkce-kdump.py script
		if not os.path.exists(self.LKCE_KDUMP_PRE_LINK):
			cmd = "cp -f " + self.LKCE_KDUMP_PRE_SCRIPT + " " + self.LKCE_KDUMP_PRE_LINK
			os.system(cmd)
	#def configure

	def status(self):
		self.check_config(self.LKCE_CONFIG_FILE)
	#def status

	def clean(self, subarg):
		if subarg == "--all":
			val = raw_input("lkce removes all the files in %s dir. do you want to proceed(yes/no)? [no]:" % (self.LKCE_OUT))
			if "yes" in val: #avoiding riskier rm -rf purposefully.
				cmd1 = "rm " + self.LKCE_OUT + "/crash*out 2> /dev/null"
				cmd2 = "find " + self.LKCE_OUT + " -name vmlinux | xargs rm 2> /dev/null"
				cmd3 = "find " + self.LKCE_OUT + "/debug-vmlinux -type d -empty -delete 2> /dev/null"
				os.system(cmd1)
				os.system(cmd2)
				os.system(cmd3)
			#if "yes"
		else:
			val = raw_input("lkce deletes all but last three %s/crash*out files. do you want to proceed(yes/no)? [no]:"%(self.LKCE_OUT))
			if "yes" in val:
				cmd1 = "ls -r " + self.LKCE_OUT + "/crash*out 2>/dev/null| tail -n +4 | xargs rm 2> /dev/null"
				os.system(cmd1) #start removing from 4th entry
	#def clean

	def list(self):
		print "followings are the crash*out found in %s dir:" % self.LKCE_OUT
		for file in os.listdir(self.LKCE_OUT):
			if re.search("crash.*out", file):
				print "%s/%s"%(self.LKCE_OUT, file)
	#def list

	def usage(self):
		usage = """Usage: """ + sys.argv[0] + """ <options>
options:
	enable		-- enable lkce
	disable 	-- disable lkce
	configure [--default] 	-- configure lkce
	configure [--show] 	-- show lkce configuration
	status 		-- print status of lkce
	clean [--all]	-- clear old crash*out files
	list		-- list crash*out files
"""
		print(usage)
		sys.exit()
	#def usage
#class LKCE

def main():
	lkce = LKCE()

	if len(sys.argv) < 2:
		lkce.usage()

	arg = sys.argv[1]
	subarg = None
	if len(sys.argv) > 2:
		subarg = sys.argv[2]

	if arg == "enable":
		lkce.enable_lkce()

	elif arg == "disable":
		lkce.disable_lkce()

	elif arg == "configure":
		lkce.configure(subarg)

	elif arg == "status":
		lkce.status()

	elif arg == "clean":
		lkce.clean(subarg)

	elif arg == "list":
		lkce.list()

	else:
		lkce.usage()
#def main

if __name__ == '__main__':
    main()
