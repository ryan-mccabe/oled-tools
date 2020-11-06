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

import sys
import os
import getpass
import platform

# Oracle Linux Enhanced Diagnostic Tools
MAJOR = "0"
MINOR = "1"

BINDIR="/usr/lib/oled-tools"

# cmds
GATHER = BINDIR + "/gather"
LKCE = BINDIR + "/lkce"
SMTOOL = BINDIR + "/smtool"
OLED_KDUMP = BINDIR + "/kdump"

def dist():
    os_release = float(platform.linux_distribution()[1])
    if os_release > 6.0 and os_release < 7.0 :
        dist = "el6"
    elif os_release > 7.0 and os_release < 8.0 :
        dist = "el7"
    else :
        dist = "el8"
    return dist

def help(error):
    print("Oracle Linux Enhanced Diagnostic Tools")
    print("Usage:")
    print("  %s <command> <subcommand>" % sys.argv[0])
    print("Valid commands:")
    print("     smtool          -- Spectre-Meltdown tool")
    if (dist() != "el8") :
        print("     gather          -- system data gather")
    print("     lkce            -- Linux Kernel Core Extractor")
    print("     kdump           -- configure oled related kdump options")
    print("     help            -- show this help message")
    print("     version         -- print oled version")

    if (error):
        sys.exit(1)
    sys.exit(0)

def run_as_root():
    if (getpass.getuser()) != "root":
        print("Run as root only")
        sys.exit(1)

def cmd_version():
	version = "%s.%s"%(MAJOR, MINOR)
	print(version)

def cmd_smtool(args):
    cmdline = SMTOOL
    for arg in args:
        cmdline = cmdline + " %s" % arg
    ret = os.system(cmdline)
    return ret

def cmd_gather(args):
    cmdline = GATHER
    for arg in args:
        cmdline = cmdline + " %s" % arg
    ret = os.system(cmdline)
    return ret

def cmd_lkce(args):
    cmdline = LKCE
    for arg in args:
        cmdline = cmdline + " %s" % arg
    ret = os.system(cmdline)
    return ret

def cmd_kdump(args):
    cmdline = OLED_KDUMP
    for arg in args:
        cmdline = cmdline + " %s" % arg
    ret = os.system(cmdline)
    return ret

def cmd_help(args):
    help(False)

def main():
    run_as_root()

    if len(sys.argv) < 2:
        help(True)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "smtool":
        ret = cmd_smtool(args)
        sys.exit(ret)
    elif cmd == "gather":
        if (dist() != "el8") :
            ret = cmd_gather(args)
            sys.exit(ret)
        else :
            print ("%s not supported for this distribution" % cmd)
            sys.exit(1)
    elif cmd == "lkce":
        ret = cmd_lkce(args)
        sys.exit(ret)
    elif cmd == "kdump":
        ret = cmd_kdump(args)
        sys.exit(ret)
    elif cmd == "version" or cmd == "--version":
        ret = cmd_version()
        sys.exit(ret)
    elif cmd == "help":
        ret = cmd_help(args)
        sys.exit(ret)
    else:
        print("Invalid command")
        sys.exit(1)

    help(True)

if __name__ == "__main__":
    main()
